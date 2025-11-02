"""Consultation feedback analysis service.
Implements naive unsupervised theme extraction by frequent bigrams after stopword removal.
"""
from typing import List
from fastapi import APIRouter
from pydantic import BaseModel
import re
from collections import Counter

router = APIRouter()

class Theme(BaseModel):
    theme: str
    count: int
    sentiment: str
    policy_links: List[str] = []

class FeedbackRequest(BaseModel):
    text: str

@router.post("/cluster", response_model=List[Theme])
async def cluster_feedback(req: FeedbackRequest):
    """Extract top themes from free text using simple bigram frequency and heuristic sentiment."""
    text = (req.text or "").lower()
    if not text.strip():
        return []
    # Basic tokenization
    tokens = re.findall(r"[a-zA-Z']+", text)
    stop = set("""
        a an the of in on at to for and or if is are was were be been being with by from as this that these those it its their our your you we they he she them his her i me my mine ours yours theirs not no
    """.split())
    toks = [t for t in tokens if t not in stop and len(t) > 2]
    bigrams = [f"{toks[i]} {toks[i+1]}" for i in range(len(toks)-1)] if len(toks) > 1 else []
    freq = Counter(bigrams)
    top = freq.most_common(5)
    themes: List[Theme] = []
    for phrase, count in top:
        sentiment = "negative" if any(w in phrase for w in ["concern", "object", "oppose", "traffic", "noise"]) else "positive"
        themes.append(Theme(theme=phrase.title(), count=count, sentiment=sentiment, policy_links=[]))
    return themes
