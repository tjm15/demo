"""Embedding utilities using sentence-transformers.
Falls back gracefully if model is unavailable.
"""
from __future__ import annotations
from typing import List
import os

_MODEL = None
_MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
_DIM_TARGET = int(os.getenv("EMBED_DIM", "1024"))


def _load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    try:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer(_MODEL_NAME)
    except Exception as e:
        _MODEL = None
    return _MODEL


def _pad_or_truncate(vec: List[float], dim: int) -> List[float]:
    if len(vec) == dim:
        return vec
    if len(vec) > dim:
        return vec[:dim]
    # pad with zeros
    return vec + [0.0] * (dim - len(vec))


def get_embedding(text: str) -> List[float]:
    """Return an EMBED_DIM-dimensional embedding for the given text.
    If the model is not available, return a deterministic fallback embedding
    derived from hashing tokens (so that vector queries still work deterministically).
    """
    model = _load_model()
    if model is not None:
        try:
            vec = model.encode([text], normalize_embeddings=True)[0].tolist()
            return _pad_or_truncate(vec, _DIM_TARGET)
        except Exception:
            pass
    # Fallback deterministic embedding via hashing
    import hashlib
    import math
    tokens = text.lower().split()
    out = [0.0] * _DIM_TARGET
    for tok in tokens:
        h = hashlib.sha256(tok.encode()).digest()
        for i in range(0, len(h), 4):
            idx = (h[i] + h[i+1]) % _DIM_TARGET
            val = int.from_bytes(h[i:i+4], 'little') / (2**32 - 1)
            out[idx] += (val - 0.5)
    # L2 normalize
    norm = math.sqrt(sum(v*v for v in out)) or 1.0
    out = [v / norm for v in out]
    return out
