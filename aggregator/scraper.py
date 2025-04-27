from scrapy.crawler import CrawlerProcess
from .scrape import SPIDERS
from .database import connect, insert_article
from .embeddings import embed
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLitePipeline:
    def __init__(self):
        self.conn = connect()
        logger.info("SQLite pipeline initialized")

    def process_item(self, item, spider):
        try:
            logger.info(f"Processing item from {item['source']}: {item['title']}")
            item["embedding"] = embed(item["content"])
            insert_article(self.conn, item)
            logger.info("Item successfully processed and stored")
            return item
        except Exception as e:
            logger.error(f"Error processing item: {str(e)}")
            raise


def run():
    settings = {
        "LOG_ENABLED": True,
        "LOG_LEVEL": "INFO",
        "ITEM_PIPELINES": {SQLitePipeline: 300},
        "DOWNLOAD_TIMEOUT": 30,
        "ROBOTSTXT_OBEY": False,
    }
    logger.info("Starting the scraping process")
    process = CrawlerProcess(settings)
    for sp in SPIDERS:
        logger.info(f"Adding spider: {sp.name}")
        process.crawl(sp)
    process.start()
    logger.info("Scraping process completed") 