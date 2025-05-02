from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Subscription
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_valid_email(email):
    """Check if email is valid."""
    # Basic email validation regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def clean_email(email):
    """Clean up email address by removing any trailing timestamps or dashes."""
    # Remove any timestamps or dashes that got appended to the email
    email = re.sub(r'\d{2}:\d{2}:\d{2}\.\d+$', '', email)
    email = re.sub(r'-+$', '', email)
    # Remove any trailing timestamps in the middle of the email
    email = re.sub(r'\d{2}:\d{2}:\d{2}\.\d+(?=@)', '', email)
    # Remove any non-standard characters
    email = re.sub(r'[^\w\.-@]', '', email)
    email = email.strip()
    return email

def remove_invalid_emails():
    """Remove invalid email addresses from the database."""
    # Create database connection
    engine = create_engine('sqlite:///news.db')
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create session
    db = SessionLocal()
    try:
        # Get all active subscriptions
        subscriptions = db.query(Subscription).filter_by(is_active=True).all()
        
        invalid_count = 0
        for subscription in subscriptions:
            clean_addr = clean_email(subscription.email)
            if not is_valid_email(clean_addr):
                logger.info(f"Removing invalid email: {subscription.email}")
                db.delete(subscription)
                invalid_count += 1
        
        if invalid_count > 0:
            db.commit()
            logger.info(f"Successfully removed {invalid_count} invalid email addresses")
        else:
            logger.info("No invalid email addresses found")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing invalid emails: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    remove_invalid_emails() 