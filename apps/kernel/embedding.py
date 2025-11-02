"""Embedding utilities: sentence-transformers with 1024-d padding.

Loads a local sentence-transformers model and exposes embed(text) -> list[float] of length 1024.
"""
from functools import lru_cache
from typing import List

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dims
TARGET_DIM = 1024

@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)

def _pad_or_truncate(vec: List[float], dim: int = TARGET_DIM) -> List[float]:
    if len(vec) == dim:
        return vec
    if len(vec) > dim:
        return vec[:dim]
    # pad with zeros
    return vec + [0.0] * (dim - len(vec))

def embed(text: str) -> List[float]:
    model = _get_model()
    v = model.encode([text], normalize_embeddings=True)[0].tolist()
    return _pad_or_truncate(v, TARGET_DIM)
