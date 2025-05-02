from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH   = BASE_DIR / "news.db"

# LLM back‑ends
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "aya:8b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Embeddings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBED_DIM       = 384

# Retrieval
MAX_CONTEXT_ARTICLES = 5
SIM_THRESHOLD        = 0.15 