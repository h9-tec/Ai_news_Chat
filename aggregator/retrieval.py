from __future__ import annotations
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Dict, Any
from .database import connect, fetch_all_articles
from .embeddings import bytes_to_vec, get_model
from .config import MAX_CONTEXT_ARTICLES, SIM_THRESHOLD
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

def sort_by_source_priority(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort articles by source priority and similarity (or timestamp if similarity is missing)"""
    # Define source priority (higher number = higher priority)
    source_priority = {
        "smol.ai": 3,
        "TechCrunch": 2,
        "HuggingFace": 1
    }
    
    # Group articles by source
    source_groups = defaultdict(list)
    for article in articles:
        source_groups[article["source"]].append(article)
    
    # Sort within each source group
    for source in source_groups:
        if all("similarity" in x for x in source_groups[source]):
            # Sort by similarity if present
            source_groups[source].sort(key=lambda x: x["similarity"], reverse=True)
        else:
            # Otherwise, sort by timestamp (most recent first)
            source_groups[source].sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    
    # Combine results with priority sources first
    sorted_articles = []
    for source, priority in sorted(source_priority.items(), key=lambda x: x[1], reverse=True):
        if source in source_groups:
            sorted_articles.extend(source_groups[source])
    
    # Add any remaining sources
    for source, articles in source_groups.items():
        if source not in source_priority:
            sorted_articles.extend(articles)
            
    return sorted_articles

def retrieve(query: str, k: int = MAX_CONTEXT_ARTICLES) -> List[Dict[str, Any]]:
    """Retrieve relevant articles for a query"""
    try:
        # Get all articles
        conn = connect()
        rows = fetch_all_articles(conn)
        if not rows:
            logger.warning("No articles found in database")
            return []

        # Unpack article data
        sources, titles, contents, blobs, timestamps, urls, authors = zip(*rows)
        
        # Convert embeddings
        try:
            vecs = np.vstack([bytes_to_vec(b) for b in blobs])
        except Exception as e:
            logger.error(f"Error converting embeddings: {e}")
            return []

        # Get query embedding
        try:
            qv = get_model().encode([query], convert_to_numpy=True)[0]
        except Exception as e:
            logger.error(f"Error encoding query: {e}")
            return []

        # Calculate similarities
        sims = cosine_similarity([qv], vecs)[0]
        
        # Get all matches above threshold
        results = []
        for i, sim in enumerate(sims):
            if sim < SIM_THRESHOLD:
                continue
            results.append({
                "source": sources[i],
                "title": titles[i],
                "content": contents[i],
                "timestamp": timestamps[i],
                "url": urls[i],
                "author": authors[i],
                "similarity": float(sim)
            })
        
        # Sort by source priority and similarity
        results = sort_by_source_priority(results)
        
        # Take top k results after sorting
        results = results[:k]
            
        # Log results
        source_counts = defaultdict(int)
        for r in results:
            source_counts[r["source"]] += 1
        logger.info(f"Found {len(results)} relevant articles for query: {query[:50]}...")
        logger.info(f"Source distribution: {dict(source_counts)}")
        
        return results

    except Exception as e:
        logger.error(f"Error in retrieval: {e}")
        return [] 