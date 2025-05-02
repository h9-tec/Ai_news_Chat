from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Subscription
from sqlalchemy import func
import re

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

def format_datetime(dt):
    """Format datetime in a consistent way."""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return "N/A"

def view_subscribers():
    # Create database connection
    engine = create_engine('sqlite:///news.db')
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create session
    db = SessionLocal()
    try:
        # Get unique email addresses with their earliest subscription date
        subquery = db.query(
            Subscription.email,
            func.min(Subscription.created_at).label('first_subscription'),
            func.max(Subscription.updated_at).label('last_update')
        ).filter_by(is_active=True)\
         .group_by(Subscription.email)\
         .all()
        
        if not subquery:
            print("No active subscribers found.")
            return
        
        # Clean up emails and ensure uniqueness
        cleaned_subscribers = []
        invalid_subscribers = []
        seen_emails = set()
        
        for email, created, updated in subquery:
            clean_addr = clean_email(email)
            if clean_addr and '@' in clean_addr and clean_addr not in seen_emails:
                seen_emails.add(clean_addr)
                if is_valid_email(clean_addr):
                    cleaned_subscribers.append((clean_addr, created, updated))
                else:
                    invalid_subscribers.append((clean_addr, created, updated))
        
        # Sort by subscription date
        unique_subscribers = sorted(cleaned_subscribers, key=lambda x: x[1])
        invalid_subscribers = sorted(invalid_subscribers, key=lambda x: x[1])
        
        if invalid_subscribers:
            print("\nINVALID EMAIL ADDRESSES (These will cause email sending to fail):")
            print("-" * 50)
            for email, created_at, updated_at in invalid_subscribers:
                print(f"Invalid Email: {email}")
                print(f"First subscribed at: {format_datetime(created_at)}")
                print(f"Last updated: {format_datetime(updated_at)}")
                print("-" * 50)
        
        print("\nValid Active Subscribers:")
        print("-" * 50)
        for email, created_at, updated_at in unique_subscribers:
            print(f"Email: {email}")
            print(f"First subscribed at: {format_datetime(created_at)}")
            print(f"Last updated: {format_datetime(updated_at)}")
            print("-" * 50)
            
        print(f"\nTotal valid subscribers: {len(unique_subscribers)}")
        if invalid_subscribers:
            print(f"Total invalid subscribers: {len(invalid_subscribers)}")
            
    finally:
        db.close()

if __name__ == "__main__":
    view_subscribers() 