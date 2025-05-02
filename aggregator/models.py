from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean

from .database import Base

class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    subscribed_at = Column(DateTime, default=datetime.utcnow)
    last_email_sent = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Subscriber {self.email}>" 