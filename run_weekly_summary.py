from aggregator.email_service import EmailService
from aggregator.llm import LLM
from aggregator.database import connect, fetch_recent
from aggregator.retrieval import sort_by_source_priority
from collections import defaultdict
from datetime import datetime, date
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def ensure_source_diversity(articles, max_per_source: int = 10):
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

def run_weekly_summary():
    try:
        # Log backend and model for debugging
        logger.info(f"LLM_BACKEND env: {os.getenv('LLM_BACKEND')}")
        logger.info(f"GEMINI_MODEL env: {os.getenv('GEMINI_MODEL')}")
        # Initialize services
        email_service = EmailService()
        llm = LLM(backend=os.getenv("LLM_BACKEND", "gemini"))
        
        # Get latest articles using the same connection as QA
        conn = connect()
        rows = fetch_recent(conn, days=7)
        
        if not rows:
            logger.info("No new articles to summarize for weekly digest")
            return
            
        logger.info(f"Found {len(rows)} articles to summarize for weekly digest")
        
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
        
        # Sort by source priority and ensure diversity
        articles = sort_by_source_priority(articles)
        articles = ensure_source_diversity(articles)
        
        # --- Map step: Summarize in chunks ---
        chunk_size = 2  # You can adjust this for your LLM's context window
        chunk_summaries = []
        for i in range(0, len(articles), chunk_size):
            chunk = articles[i:i+chunk_size]
            chunk_content = "\n\n".join(f"{a['title']}\n{a['content'][:2000]}" for a in chunk)
            chunk_prompt = f"""Summarize the following AI news articles from the past week.\n\nWrite detailed bullet points for each major highlight, insight, or development.\nDo NOT include source citations or URLs.\n\nNews Content:\n{chunk_content}\n"""
            chunk_summary = llm.generate(chunk_prompt, max_tokens=700)
            chunk_summaries.append(chunk_summary.strip())
            logger.info(f"Generated summary chunk {i//chunk_size + 1} of {(len(articles) + chunk_size - 1)//chunk_size}")
        
        # --- Reduce step: Aggregate all chunk summaries ---
        all_chunk_summaries = "\n\n".join(chunk_summaries)
        today = date.today().isoformat()
        final_prompt = f"""WEEKLY AI NEWS SUMMARY - {today}\n\nRead the following summaries of AI news from the past 7 days.\n\n- Write at least 20 detailed bullet points, each covering a distinct news highlight, insight, or development.\n- Each bullet point should be detailed and reflect the depth of the news, not just headlines.\n- Cover all major topics, trends, and events.\n- Do NOT include source citations or URLs.\n- The summary should be comprehensive and easy to scan.\n\nChunk Summaries:\n{all_chunk_summaries}\n"""
        summary = llm.generate(final_prompt, max_tokens=1800)
        
        # Ensure proper markdown formatting
        if not summary.startswith("WEEKLY AI NEWS SUMMARY"):
            summary = f"WEEKLY AI NEWS SUMMARY - {today}\n\n{summary}"
        
        # Send the weekly digest with the generated summary
        article_objects = [{
            'title': 'Weekly AI News Summary',
            'content': summary,
            'source': 'AI News Aggregator',
            'url': ''
        }]
        
        # Generate summaries and send email
        email_service.send_digest(articles=article_objects, is_weekly=True)
        logger.info("Successfully sent weekly summary!")
            
    except Exception as e:
        logger.error(f"Failed to run weekly summary: {str(e)}")
        raise

if __name__ == "__main__":
    run_weekly_summary() 