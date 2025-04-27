from __future__ import annotations
from sentence_transformers import SentenceTransformer
import numpy as np
from .config import EMBEDDING_MODEL, EMBED_DIM

_model: SentenceTransformer | None = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed(text: str) -> bytes:
    vec = get_model().encode([text])[0].astype(np.float32)
    return vec.tobytes()


def bytes_to_vec(blob: bytes):
    return np.frombuffer(blob, dtype=np.float32, count=EMBED_DIM) 