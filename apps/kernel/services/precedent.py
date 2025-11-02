"""Precedent search service - hybrid text + vector search backed by Postgres."""
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from db import get_conn, to_vector
from modules.embedding import get_embedding

router = APIRouter()

class Precedent(BaseModel):
    case_ref: str
    decision: str
    similarity: float
    key_point: str
    date: Optional[str] = None

class PrecedentSearchRequest(BaseModel):
    query: str
    limit: int = 5

@router.post("/search", response_model=List[Precedent])
async def search_precedents(req: PrecedentSearchRequest):
    """Hybrid search over precedents (summary text + embedding)."""
    q = req.query.strip()
    if not q:
        return []

    rows: List[Precedent] = []
    q_emb = get_embedding(q)
    sql = """
        SELECT case_ref,
               decision,
               decision_date,
               summary,
               ts_rank_cd(tsv, plainto_tsquery('english', %s)) AS rank_txt,
               (1 - (embedding <=> %s::vector)) AS rank_vec,
               (0.6 * COALESCE(ts_rank_cd(tsv, plainto_tsquery('english', %s)), 0) +
                0.4 * COALESCE(1 - (embedding <=> %s::vector), 0)) AS score
        FROM precedent
        WHERE (tsv @@ plainto_tsquery('english', %s)) OR (embedding IS NOT NULL)
        ORDER BY score DESC
        LIMIT %s
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (q, to_vector(q_emb), q, to_vector(q_emb), q, req.limit))
                for case_ref, decision, decision_date, summary, rank_txt, rank_vec, score in cur.fetchall():
                    rows.append(Precedent(
                        case_ref=case_ref,
                        decision=decision,
                        similarity=float(score or 0.0),
                        key_point=(summary or '')[:140] + ("…" if summary and len(summary) > 140 else ""),
                        date=str(decision_date) if decision_date else None,
                    ))
    except Exception:
        # Fallback to ILIKE search if full-text or vector ops unavailable
        ilike = f"%{q}%"
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT case_ref, decision, decision_date, summary FROM precedent WHERE summary ILIKE %s LIMIT %s",
                    (ilike, req.limit),
                )
                for case_ref, decision, decision_date, summary in cur.fetchall():
                    rows.append(Precedent(
                        case_ref=case_ref,
                        decision=decision,
                        similarity=0.5,
                        key_point=summary[:140] + ("…" if summary and len(summary) > 140 else ""),
                        date=str(decision_date) if decision_date else None,
                    ))
    return rows
