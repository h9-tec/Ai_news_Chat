import os
from typing import List
from mailjet_rest import Client
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Subscription, NewsArticle, Category
from .llm import LLM
import logging
import json

logger = logging.getLogger(__name__)

# Initialize database connection
engine = create_engine('sqlite:///news.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize LLM for summarization
llm = LLM(backend=os.getenv("LLM_BACKEND", "gemini"))

class EmailService:
    def __init__(self):
        self.api_key = os.getenv('MAILJET_API_KEY')
        self.api_secret = os.getenv('MAILJET_API_SECRET')
        if not self.api_key or not self.api_secret:
            raise ValueError("Mailjet API credentials not found in environment variables")
        
        self.mailjet = Client(auth=(self.api_key, self.api_secret), version='v3.1')
        self.sender_email = os.getenv('SENDER_EMAIL', 'your-verified-sender@domain.com')
        self.sender_name = os.getenv('SENDER_NAME', 'AI News Weekly Digest')

    def get_latest_articles(self, days: int = 7) -> List[NewsArticle]:
        """Get articles from the last 7 days."""
        db = SessionLocal()
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            articles = db.query(NewsArticle).filter(
                NewsArticle.created_at >= cutoff_time
            ).order_by(NewsArticle.created_at.desc()).all()
            return articles
        finally:
            db.close()

    def get_active_subscribers(self) -> List[Subscription]:
        """Get all active subscribers."""
        db = SessionLocal()
        try:
            subscribers = db.query(Subscription).filter(
                Subscription.is_active == True
            ).all()
            return subscribers
        finally:
            db.close()

    def generate_arabic_summary(self, article) -> str:
        """Generate Arabic summary for an article."""
        # Handle both NewsArticle objects and dictionaries
        title = article.title if hasattr(article, 'title') else article['title']
        content = article.content if hasattr(article, 'content') else article['content']
        
        # Combine title and content for summarization
        text_to_summarize = f"Title: {title}\n\nContent: {content}"
        return llm.summarize_arabic(text_to_summarize)

    def format_email_content(self, articles: List[NewsArticle], is_weekly: bool = True) -> str:
        """Format articles into HTML email content."""
        digest_type = "الأسبوعي" if is_weekly else "اليومي"
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .article {{ margin-bottom: 20px; padding: 15px; border: 1px solid #eee; }}
                .title {{ color: #2c3e50; font-size: 18px; margin-bottom: 10px; }}
                .summary {{ color: #34495e; white-space: pre-wrap; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #7f8c8d; }}
            </style>
        </head>
        <body dir="rtl">
            <h1>📰 ملخص أخبار الذكاء الاصطناعي {digest_type}</h1>
        """

        for article in articles:
            # Handle both NewsArticle objects and dictionaries
            title = article.title if hasattr(article, 'title') else article['title']
            content = article.content if hasattr(article, 'content') else article['content']
            source = article.source if hasattr(article, 'source') else article['source']
            
            html_content += f"""
            <div class="article">
                <div class="title">{title}</div>
                <div class="summary">{content}</div>
                <div class="source">المصدر: {source}</div>
            </div>
            """

        html_content += f"""
            <div class="footer">
                <p>تم إرسال هذا البريد الإلكتروني تلقائياً. يمكنك إلغاء الاشتراك في أي وقت.</p>
                <p>© {datetime.now().year} AI News Weekly Digest</p>
            </div>
        </body>
        </html>
        """
        return html_content

    def send_digest(self, articles=None, is_weekly: bool = True):
        """Send weekly or daily digest to all active subscribers in batches of 50."""
        try:
            # Get latest articles and active subscribers
            if articles is None:
                articles = self.get_latest_articles(days=7 if is_weekly else 1)
            subscribers = self.get_active_subscribers()

            if not articles:
                logger.info("No new articles to send")
                return

            if not subscribers:
                logger.info("No active subscribers")
                return

            # Generate email content
            html_content = self.format_email_content(articles, is_weekly)
            digest_type = "الأسبوعي" if is_weekly else "اليومي"

            # Send in batches of 50
            batch_size = 50
            total = len(subscribers)
            for i in range(0, total, batch_size):
                batch = subscribers[i:i+batch_size]
                data = {
                    'Messages': [
                        {
                            "From": {
                                "Email": self.sender_email,
                                "Name": self.sender_name
                            },
                            "To": [
                                {
                                    "Email": subscriber.email,
                                    "Name": subscriber.email.split('@')[0]
                                }
                                for subscriber in batch
                            ],
                            "Subject": f"ملخص أخبار الذكاء الاصطناعي {digest_type} - {datetime.now().strftime('%Y-%m-%d')}",
                            "HTMLPart": html_content
                        }
                    ]
                }
                result = self.mailjet.send.create(data=data)
                if result.status_code == 200:
                    logger.info(f"Successfully sent {digest_type} digest to batch {i//batch_size+1} ({len(batch)} recipients)")
                else:
                    logger.error(f"Failed to send {digest_type} digest to batch {i//batch_size+1}: {result.json()}")

        except Exception as e:
            logger.error(f"Error sending digest: {str(e)}")
            raise

    def send_simple_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send a simple HTML email to a single recipient."""
        data = {
            'Messages': [
                {
                    "From": {
                        "Email": self.sender_email,
                        "Name": self.sender_name
                    },
                    "To": [
                        {
                            "Email": to_email,
                            "Name": to_email.split('@')[0]
                        }
                    ],
                    "Subject": subject,
                    "HTMLPart": html_body
                }
            ]
        }
        try:
            result = self.mailjet.send.create(data=data)
            if result.status_code == 200:
                logger.info(f"Successfully sent email to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}: {result.json()}")
                return False
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False

def send_weekly_digest():
    """Function to be called by scheduler."""
    try:
        email_service = EmailService()
        email_service.send_digest(is_weekly=True)
    except Exception as e:
        logger.error(f"Failed to send weekly digest: {str(e)}")
        raise 