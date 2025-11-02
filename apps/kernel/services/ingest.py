"""Ingestion endpoints to persist extracted paragraphs into Postgres.

This minimal ingestion creates or reuses a policy row per source URL, then inserts
paragraphs without embeddings. It also bumps source_provenance.ingested_count when possible.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from db import get_conn

router = APIRouter()


class ParaInput(BaseModel):
    text: str
    page: Optional[int] = None
    para_ref: Optional[str] = None


class IngestParasRequest(BaseModel):
    source_url: HttpUrl
    title: Optional[str] = None
    sha256: Optional[str] = None
    domain: Optional[str] = None
    paragraphs: List[ParaInput]


class IngestParasResponse(BaseModel):
    policy_id: int
    inserted: int


@router.post("/paras", response_model=IngestParasResponse)
async def ingest_paragraphs(req: IngestParasRequest):
    if not req.paragraphs:
        raise HTTPException(status_code=400, detail="paragraphs is required")

    doc_id = _doc_id_from_url(str(req.source_url))
    title = req.title or doc_id

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Upsert policy
            cur.execute("SELECT id FROM policy WHERE doc_id = %s", (doc_id,))
            row = cur.fetchone()
            if row:
                policy_id = row[0]
            else:
                cur.execute(
                    """
                    INSERT INTO policy (doc_id, title, authority, doc_type, source_url)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (doc_id, title, req.domain or None, 'external', str(req.source_url)),
                )
                policy_id = cur.fetchone()[0]

            # Insert paragraphs
            inserted = 0
            for p in req.paragraphs:
                cur.execute(
                    """
                    INSERT INTO policy_para (policy_id, para_ref, text, page)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (policy_id, p.para_ref or None, p.text, p.page),
                )
                inserted += 1

            # Bump provenance if sha256 provided
            if req.sha256:
                cur.execute(
                    "UPDATE source_provenance SET ingested_count = COALESCE(ingested_count,0) + %s WHERE sha256 = %s",
                    (inserted, req.sha256),
                )
        conn.commit()

    return IngestParasResponse(policy_id=policy_id, inserted=inserted)


def _doc_id_from_url(url: str) -> str:
    # Create a stable doc_id from URL
    try:
        from urllib.parse import urlparse
        u = urlparse(url)
        base = (u.netloc + u.path).strip('/').replace('/', '_')
        return base[:200] if base else "external_doc"
    except Exception:
        return "external_doc"
