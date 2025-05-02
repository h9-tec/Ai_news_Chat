from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class NewsArticle(Base):
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(500), unique=True, nullable=False)
    source = Column(String(100), nullable=False)
    published_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    categories = relationship("Category", secondary="article_categories", back_populates="articles")
    embeddings = relationship("ArticleEmbedding", back_populates="article", uselist=False)

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    articles = relationship("NewsArticle", secondary="article_categories", back_populates="categories")

class ArticleCategory(Base):
    __tablename__ = 'article_categories'
    
    article_id = Column(Integer, ForeignKey('news_articles.id'), primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'), primary_key=True)

class ArticleEmbedding(Base):
    __tablename__ = 'article_embeddings'
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('news_articles.id'), unique=True)
    embedding = Column(Text, nullable=False)  # Store as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    article = relationship("NewsArticle", back_populates="embeddings")

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    preferences = relationship("SubscriptionPreference", back_populates="subscription")

class SubscriptionPreference(Base):
    __tablename__ = 'subscription_preferences'
    
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'))
    category_id = Column(Integer, ForeignKey('categories.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="preferences")
    category = relationship("Category") 