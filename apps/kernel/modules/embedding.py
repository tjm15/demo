"""Embedding utilities using Ollama or sentence-transformers.
Falls back gracefully if model is unavailable.
"""
from __future__ import annotations
from typing import List
import os
import asyncio

_MODEL = None
_MODEL_NAME = os.getenv("EMBED_MODEL", "qwen3-embedding:8b")
_DIM_TARGET = int(os.getenv("EMBED_DIM", "1024"))
_EMBED_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
_OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")


def _load_model():
    """Load sentence-transformers model (fallback only)."""
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
    
    Supports:
    - Ollama models (qwen3-embedding:8b, etc.) via /api/embeddings endpoint
    - sentence-transformers as fallback
    - Deterministic hash-based fallback if both fail
    """
    
    # Try Ollama first if configured
    if _EMBED_PROVIDER == "ollama":
        try:
            import aiohttp
            import json
            
            # Ollama embeddings endpoint
            url = f"{_OLLAMA_BASE}/api/embeddings"
            payload = {"model": _MODEL_NAME, "prompt": text}
            
            # Run async request in sync context
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            async def _fetch():
                timeout = aiohttp.ClientTimeout(total=30, connect=3)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, json=payload) as resp:
                        resp.raise_for_status()
                        data = await resp.json()
                        return data.get("embedding", [])
            
            vec = loop.run_until_complete(_fetch())
            if vec:
                return _pad_or_truncate(vec, _DIM_TARGET)
        except Exception as e:
            print(f"[Embedding] Ollama embedding failed: {e}, falling back")
            pass
    
    # Try sentence-transformers
    model = _load_model()
    if model is not None:
        try:
            vec = model.encode([text], normalize_embeddings=True)[0].tolist()
            return _pad_or_truncate(vec, _DIM_TARGET)
        except Exception:
            pass
    
    # Final fallback: deterministic hash-based embedding
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
