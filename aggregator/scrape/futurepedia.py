from datetime import datetime
import time
from .base import BaseNewsSpider
import logging
import re

logger = logging.getLogger(__name__)

class FuturepediaSpider(BaseNewsSpider):
    name = "futurepedia"
    start_urls = ["https://www.futurepedia.io/ai-tools"]
    custom_settings = {
        "DOWNLOAD_TIMEOUT": 30,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "ROBOTSTXT_OBEY": False
    }

    def parse(self, response):
        logger.info(f"Parsing Futurepedia tools page: {response.url}")
        # Each tool card is a link inside a grid, e.g. <a href="/tool/xyz" ...>
        tool_cards = response.css('a[href^="/tool/"]')
        logger.info(f"Found {len(tool_cards)} tool cards")
        for card in tool_cards:
            tool_url = response.urljoin(card.attrib.get('href'))
            yield response.follow(tool_url, callback=self.parse_tool)

        # Pagination: look for next page
        next_page = response.css('a[aria-label="Go to next page"], a[rel="next"]::attr(href)').get()
        if next_page:
            logger.info(f"Following next page: {next_page}")
            yield response.follow(next_page, callback=self.parse)

    def parse_tool(self, response):
        logger.info(f"Parsing tool page: {response.url}")
        try:
            # Tool name
            title = response.css('h1::text').get() or response.css('title::text').get() or '(no title)'
            # Description
            desc = response.css('meta[name="description"]::attr(content)').get()
            if not desc:
                desc = response.css('p::text').get() or ''
            # Tags/categories
            tags = response.css('a[href^="/ai-tools/"]::text').getall()
            tags = [t.strip() for t in tags if t.strip()]
            # Published time (not available, use now)
            ts = int(time.time())
            # Content (full text)
            content_parts = response.css('div.prose *::text').getall()
            content = '\n'.join([p.strip() for p in content_parts if p.strip()])
            if not content:
                content = desc
            logger.info(f"Extracted tool: {title[:50]}...")
            yield {
                "source": "Futurepedia",
                "title": title.strip(),
                "author": None,
                "published_ts": ts,
                "url": response.url,
                "content": content.strip(),
                "tags": tags
            }
        except Exception as e:
            logger.error(f"Error processing tool page {response.url}: {str(e)}")
            return 