from __future__ import annotations
from .retrieval import retrieve, sort_by_source_priority
from .prompts import CHAT_TMPL, SUMMARY_TMPL
from .llm import LLM
from .database import connect, fetch_recent
import datetime
import logging
from typing import List, Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

def format_article_for_context(article: Dict[str, Any]) -> str:
    """Format an article for the context section of the prompt"""
    date = datetime.datetime.fromtimestamp(article["timestamp"]).strftime("%Y-%m-%d")
    return f"""
Title: {article["title"]}
Source: {article["source"]}
Date: {date}
Author: {article["author"] or "Unknown"}
Content: {article["content"][:2000]}...
URL: {article["url"]}
"""

CHAT_DEEP_TMPL = """
You are an expert AI news analyst. Given the following articles, answer the user's question in detail, synthesizing information from all relevant articles. Dive deep into the content, provide explanations, and reference specific points, arguments, or findings. Avoid superficial answers.

Articles:
{articles}

Question:
{question}

Detailed Answer:
"""

def answer(question: str, backend: str = "ollama") -> str:
    try:
        # Get relevant articles
        matches = retrieve(question)
        logger.info(f"[QA] Retrieved {len(matches)} articles for question: {question}")
        for art in matches:
            logger.info(f"[QA] Article: {art.get('title')} | ts={art.get('timestamp')} | url={art.get('url')}")
        if not matches:
            return "عذراً، لم أجد أي مقالات ذات صلة بسؤالك. يرجى المحاولة مرة أخرى لاحقاً أو طرح سؤال مختلف."

        # --- Map step: Summarize/analyze in chunks ---
        chunk_size = 2  # You can adjust this for your LLM's context window
        chunk_analyses = []
        for i in range(0, len(matches), chunk_size):
            chunk = matches[i:i+chunk_size]
            chunk_articles = "\n---\n".join(format_article_for_context(article) for article in chunk)
            chunk_prompt = f"""
You are an expert AI news analyst. Given the following articles, answer the user's question in detail, synthesizing information from all relevant articles. Dive deep into the content, provide explanations, and reference specific points, arguments, or findings. Avoid superficial answers.

Articles:
{chunk_articles}

Question:
{question}

Detailed, content-rich answer (with as much detail as possible):
"""
            chunk_analysis = LLM(backend).generate(chunk_prompt, max_tokens=900)
            chunk_analyses.append(chunk_analysis.strip())

        # --- Reduce step: Aggregate all chunk analyses ---
        all_chunk_analyses = "\n\n".join(chunk_analyses)
        final_prompt = f"""
You are an expert AI news analyst. Given the following detailed analyses of news articles, synthesize a final, deep, content-rich answer to the user's question. Dive into the details, provide explanations, and reference specific points, arguments, or findings. Avoid superficial answers.

Analyses:
{all_chunk_analyses}

Question:
{question}

Final, comprehensive answer:
"""
        response = LLM(backend).generate(final_prompt, max_tokens=1200)
        if not response or response.isspace():
            return "عذراً، حدث خطأ في معالجة السؤال. يرجى المحاولة مرة أخرى."
        return response

    except Exception as e:
        logger.error(f"[QA] Error answering question: {str(e)}")
        return "عذراً، حدث خطأ في معالجة السؤال. يرجى المحاولة مرة أخرى."

def format_article_for_summary(article: Dict[str, Any]) -> str:
    """Format an article for the summary section"""
    return f"""• {article["title"]}
  Source: {article["source"]}
  Author: {article["author"] or "Unknown"}
  Summary: {article["content"][:200]}...
  URL: {article["url"]}
"""

def ensure_source_diversity(articles: List[Dict[str, Any]], max_per_source: int = 10) -> List[Dict[str, Any]]:
    """Ensure we have a diverse set of sources in our summary"""
    source_groups = defaultdict(list)
    for article in articles:
        source_groups[article["source"]].append(article)
    
    # Take top N from each source
    diverse_articles = []
    for source in source_groups:
        diverse_articles.extend(source_groups[source][:max_per_source])
    
    # Sort by timestamp
    diverse_articles.sort(key=lambda x: x["timestamp"], reverse=True)
    return diverse_articles

def summary_today(backend: str = "ollama") -> str:
    try:
        # Get articles from the last 7 days (debugging window)
        conn = connect()
        rows = fetch_recent(conn, days=7)
        logger.info(f"[QA] Fetched {len(rows)} articles for the last 7 days summary.")
        for row in rows:
            logger.info(f"[QA] Summary Article: {row[1]} | ts={row[4]} | url={row[5]}")
        if not rows:
            return "لم يتم العثور على أخبار للأيام الماضية. يرجى المحاولة لاحقاً."
            
        # Convert rows to article dictionaries
        articles = [
            {
                "source": src,
                "title": title,
                "content": content,
                "timestamp": ts,
                "url": url,
                "author": author
            }
            for src, title, content, _, ts, url, author in rows
        ]
        
        # Sort by source priority first
        articles = sort_by_source_priority(articles)
        
        # Ensure source diversity
        articles = ensure_source_diversity(articles)
        
        # --- Map step: Summarize in chunks ---
        chunk_size = 2  # You can adjust this for your LLM's context window
        chunk_summaries = []
        for i in range(0, len(articles), chunk_size):
            chunk = articles[i:i+chunk_size]
            chunk_content = "\n\n".join(f"{a['title']}\n{a['content'][:2000]}" for a in chunk)
            chunk_prompt = f"""Summarize the following AI news articles from the past week.\n\nWrite detailed bullet points for each major highlight, insight, or development.\nDo NOT include source citations or URLs.\n\nNews Content:\n{chunk_content}\n"""
            chunk_summary = LLM(backend).generate(chunk_prompt, max_tokens=700)
            chunk_summaries.append(chunk_summary.strip())
        
        # --- Reduce step: Aggregate all chunk summaries ---
        all_chunk_summaries = "\n\n".join(chunk_summaries)
        today = datetime.date.today().isoformat()
        final_prompt = f"""WEEKLY AI NEWS SUMMARY - {today}\n\nRead the following summaries of AI news from the past 7 days.\n\n- Write at least 20 detailed bullet points, each covering a distinct news highlight, insight, or development.\n- Each bullet point should be detailed and reflect the depth of the news, not just headlines.\n- Cover all major topics, trends, and events.\n- Do NOT include source citations or URLs.\n- The summary should be comprehensive and easy to scan.\n\nChunk Summaries:\n{all_chunk_summaries}\n"""
        summary = LLM(backend).generate(final_prompt, max_tokens=1800)
        if not summary or summary.isspace():
            return "عذراً، حدث خطأ في إنشاء الملخص. يرجى المحاولة مرة أخرى."
        
        # Ensure proper markdown formatting
        if not summary.startswith("WEEKLY AI NEWS SUMMARY"):
            summary = f"WEEKLY AI NEWS SUMMARY - {today}\n\n{summary}"
            
        return summary
        
    except Exception as e:
        logger.error(f"[QA] Error generating summary: {str(e)}")
        return "عذراً، حدث خطأ في إنشاء الملخص. يرجى المحاولة مرة أخرى." 