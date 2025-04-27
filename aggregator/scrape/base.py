import scrapy, bs4, time
from datetime import datetime
from typing import Generator

class BaseNewsSpider(scrapy.Spider):
    custom_settings = {
        "DOWNLOAD_TIMEOUT": 15,
        "USER_AGENT": "newsbot/0.1",
    }

    def parse_article(self, response, source: str):
        soup = bs4.BeautifulSoup(response.text, "lxml")
        paragraphs = "\n".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
        title = soup.find("title").get_text() if soup.title else response.url
        yield {
            "source": source,
            "title": title.strip(),
            "author": None,
            "published_ts": int(time.time()),
            "url": response.url,
            "content": paragraphs,
        } 