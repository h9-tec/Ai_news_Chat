from datetime import datetime
import time, re
from .base import BaseNewsSpider
import logging

logger = logging.getLogger(__name__)

class SmolAISpider(BaseNewsSpider):
    name = "smol_ai"
    start_urls = ["https://news.smol.ai/"]
    custom_settings = {
        "DOWNLOAD_TIMEOUT": 30,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    def parse(self, response):
        logger.info(f"Parsing main page: {response.url}")
        # Find all daily issue links
        article_links = response.css('a.block.rounded-lg.border')
        logger.info(f"Found {len(article_links)} article links")
        for link in article_links:
            href = link.attrib.get('href')
            if not href or not href.startswith('/issues/'):
                continue
            article_url = response.urljoin(href)
            # Extract the date from the <time> tag inside the link
            date_str = link.css('time::attr(datetime)').get()
            # Extract the headline/title from the link
            title = link.css('div.font-semibold::text').get()
            yield response.follow(
                article_url,
                self.parse_issue,
                meta={'published_datetime': date_str, 'title': title}
            )

    def parse_issue(self, response):
        try:
            date_str = response.meta.get('published_datetime')
            title = response.meta.get('title') or '(no title)'
            if date_str:
                try:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    ts = int(date_obj.timestamp())
                except Exception:
                    ts = int(time.time())
            else:
                ts = int(time.time())

            # Focus on the main content container, avoiding navigation and repeated elements
            # Try to select the main news content, e.g., a div with class 'prose' or 'markdown-body', or <main>
            main_content = response.css('main')
            if not main_content:
                main_content = response.css('div.prose, div.markdown-body, article')
            if main_content:
                # Remove navigation, headers, and footer text if present
                # Only get text from the main content block
                content = '\n'.join(main_content[0].css('::text').getall()).strip()
            else:
                content = '\n'.join(response.css('::text').getall()).strip()

            # Remove common navigation/footer phrases if present
            for phrase in ["Back to issues", "Skip to Main", "subscribe", "tags", "Search (Cmd+K)", "See all issues", "Back to top", "© 2025 • AINews"]:
                content = content.replace(phrase, "")
            content = re.sub(r'\n+', '\n', content).strip()

            tags = response.css('code::text').getall()

            logger.info(f"Extracted issue: {title[:50]} from {response.url} | ts={ts}")

            yield {
                "source": "smol.ai",
                "title": title.strip(),
                "author": None,
                "published_ts": ts,
                "url": response.url,
                "content": content.strip(),
                "tags": tags
            }
        except Exception as e:
            logger.error(f"Error processing issue page {response.url}: {str(e)}")
            return 