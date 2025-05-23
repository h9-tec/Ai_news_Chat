"""SQLite helpers + schema management"""
from __future__ import annotations
import sqlite3, pickle, time
from typing import Dict, Any
from .config import DB_PATH, EMBED_DIM
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY,
    source TEXT,
    title TEXT,
    author TEXT,
    published_ts INTEGER,
    url TEXT UNIQUE,
    content TEXT,
    embedding BLOB
);
CREATE INDEX IF NOT EXISTS idx_date   ON articles(published_ts);
CREATE INDEX IF NOT EXISTS idx_source ON articles(source);
"""

# Create database URL
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./news.db')

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def insert_article(conn: sqlite3.Connection, item: Dict[str, Any]):
    """Insert if URL not seen"""
    try:
        with conn:
            conn.execute(
                """INSERT INTO articles(source,title,author,published_ts,url,content,embedding)
                   VALUES (:source,:title,:author,:published_ts,:url,:content,:embedding)""",
                item,
            )
    except sqlite3.IntegrityError:
        pass


def fetch_recent(conn: sqlite3.Connection, days: int = 1):
    since = int(time.time()) - days * 86400
    cur = conn.execute(
        """SELECT source, title, content, embedding, published_ts, url, author 
           FROM articles 
           WHERE published_ts >= ? 
           ORDER BY published_ts DESC""",
        (since,)
    )
    return cur.fetchall()

def fetch_all_articles(conn: sqlite3.Connection):
    """Fetch all articles for search"""
    cur = conn.execute(
        """SELECT source, title, content, embedding, published_ts, url, author 
           FROM articles 
           ORDER BY published_ts DESC"""
    )
    return cur.fetchall() 