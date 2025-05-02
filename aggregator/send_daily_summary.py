from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import Subscriber
from .qa import summary_today
from .email_service import EmailService
import logging

logger = logging.getLogger(__name__)

def send_daily_summary():
    """Generate and send daily summary to all active subscribers"""
    try:
        # Get today's summary
        summary = summary_today("groq")  # Using groq for better quality
        if not summary:
            logger.error("Failed to generate summary")
            return False

        # Get active subscribers
        with Session() as session:
            subscribers = session.query(Subscriber).filter_by(is_active=True).all()
            if not subscribers:
                logger.info("No active subscribers found")
                return True

            # Get subscriber emails
            subscriber_emails = [s.email for s in subscribers]

        # Send email
        email_service = EmailService()
        html_content = email_service.format_summary_email(summary)
        subject = f"AI News Daily Summary - {datetime.now().strftime('%B %d, %Y')}"
        
        success = email_service.send_summary_email(
            subscribers=subscriber_emails,
            subject=subject,
            html_content=html_content
        )

        if success:
            # Update last_email_sent timestamp
            with Session() as session:
                session.query(Subscriber)\
                    .filter(Subscriber.email.in_(subscriber_emails))\
                    .update({Subscriber.last_email_sent: datetime.utcnow()})
                session.commit()
            return True
        else:
            logger.error("Failed to send summary email")
            return False

    except Exception as e:
        logger.error(f"Error in send_daily_summary: {str(e)}")
        return False

if __name__ == "__main__":
    send_daily_summary() 