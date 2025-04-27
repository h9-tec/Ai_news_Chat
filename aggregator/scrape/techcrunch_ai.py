from datetime import datetime
import time
from .base import BaseNewsSpider
import logging

logger = logging.getLogger(__name__)

class TechCrunchAISpider(BaseNewsSpider):
    name = "techcrunch_ai"
    start_urls = [
        "https://techcrunch.com/tag/artificial-intelligence/",
        "https://techcrunch.com/tag/ai/",
        "https://techcrunch.com/tag/machine-learning/"
    ]
    custom_settings = {
        "DOWNLOAD_TIMEOUT": 30,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "ROBOTSTXT_OBEY": False
    }

    def parse(self, response):
        logger.info(f"Parsing tag page: {response.url}")
        
        # Articles can be in the main feed or in the "Latest" section
        articles = response.css('article.post-block')
        logger.info(f"Found {len(articles)} articles")
        
        for article in articles:
            # Get article URL
            link = article.css('h2 a::attr(href)').get()
            if not link:
                continue
                
            logger.info(f"Found article link: {link}")
            yield response.follow(link, callback=self.parse_article)
            
        # Look for "Load More" button
        next_page = response.css('a.load-more::attr(href)').get()
        if next_page:
            logger.info(f"Following next page: {next_page}")
            yield response.follow(next_page, callback=self.parse)

    def parse_article(self, response):
        logger.info(f"Parsing article: {response.url}")
        
        try:
            # Get article title
            title = response.css('h1.article__title::text').get()
            if not title:
                title = response.css('h1::text').get() or "(no title)"
            
            # Get article content - main content is in article-content div
            content_parts = response.css('div.article-content p::text, div.article-content li::text').getall()
            if not content_parts:
                content_parts = response.css('div.post-content p::text, div.post-content li::text').getall()
            content = '\n'.join([p.strip() for p in content_parts if p.strip()])
            
            # Get author
            author = response.css('a[rel="author"]::text').get()
            if not author:
                author = response.css('.article__byline::text').get()
            
            # Get timestamp
            ts_meta = response.css('meta[property="article:published_time"]::attr(content)').get()
            if ts_meta:
                ts = int(datetime.fromisoformat(ts_meta.rstrip('Z')).timestamp())
            else:
                ts = int(time.time())
            
            # Get tags
            tags = response.css('a[rel="tag"]::text').getall()
            
            logger.info(f"Extracted article: {title[:50]}...")
            
            yield {
                "source": "TechCrunch",
                "title": title.strip(),
                "author": author.strip() if author else None,
                "published_ts": ts,
                "url": response.url,
                "content": content,
                "tags": tags
            }
            
        except Exception as e:
            logger.error(f"Error processing article {response.url}: {str(e)}")
            return 