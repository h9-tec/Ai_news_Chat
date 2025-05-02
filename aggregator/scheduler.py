from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .email_service import send_weekly_digest
import logging

logger = logging.getLogger(__name__)

def setup_weekly_digest_scheduler():
    """Set up the scheduler for weekly digest emails."""
    scheduler = BackgroundScheduler()
    
    # Schedule the weekly digest to run at 8:00 AM UTC every Sunday
    scheduler.add_job(
        send_weekly_digest,
        trigger=CronTrigger(day_of_week='sun', hour=8, minute=0),
        id='weekly_digest',
        name='Send weekly AI news digest',
        replace_existing=True
    )
    
    try:
        scheduler.start()
        logger.info("Weekly digest scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        raise

if __name__ == "__main__":
    setup_weekly_digest_scheduler() 