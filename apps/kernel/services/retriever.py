"""Retriever service implementing hybrid policy retrieval with simple KG expansion.

Endpoints:
- POST /retrieve → top chunks + graph context
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any, Tuple
import json
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from db import get_conn, to_vector
from modules.embedding import get_embedding
from contracts.schemas import (
    RetrieveRequest,
    RetrieveResponse,
    ChunkItem,
    GraphContext,
)

router = APIRouter()


def _load_fixture_graph() -> Dict[str, Any]:
    p = Path("/home/tjm/code/demo/fixtures/lpa_demo/policy_graph.json")
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return {"policies": []}
    return {"policies": []}


def _kg_neighbors(policy_ids: List[str]) -> GraphContext:
    """Build a small graph context around given policy ids using fixtures.
    If DB relations exist, this can be replaced with a SQL query.
    """
    data = _load_fixture_graph()
    nodes = set()
    edges: List[Dict[str, str]] = []
    wanted = set(p.split(".")[0] for p in policy_ids if p)
    for p in data.get("policies", []):
        pid = p.get("id")
        if not pid:
            continue
        if pid in wanted or any(pid == w for w in wanted):
            nodes.add(pid)
            for dst in p.get("references", []) or []:
                nodes.add(dst)
                edges.append({"src": pid, "dst": dst, "relation": "reference"})
            for src in p.get("referenced_by", []) or []:
                nodes.add(src)
                edges.append({"src": src, "dst": pid, "relation": "reference"})
    return GraphContext(nodes=sorted(nodes), edges=edges)


def _spatial_tags(site_geom: Optional[Dict[str, Any]]) -> List[str]:
    """Return designation names overlapping the site (best-effort)."""
    if not site_geom:
        return []
    tags: List[str] = []
    # Use DB if available
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH site AS (
                      SELECT ST_Transform(ST_GeomFromGeoJSON(%s), 27700) AS g
                    )
                    SELECT DISTINCT COALESCE(l.layer_type, 'designation') || ':' || COALESCE(g.name, l.name)
                    FROM layer l
                    JOIN layer_geom g ON g.layer_id = l.id
                    CROSS JOIN site
                    WHERE ST_Intersects(g.geom, site.g)
                    LIMIT 50
                    """,
                    (json.dumps(site_geom),),
                )
                tags = [r[0] for r in cur.fetchall()]
    except Exception:
        # Silent fallback
        tags = []
    return tags


def _score_formula(bm25: float, sim: float, tag_overlap: float, boosts: float = 0.0) -> float:
    return 0.5 * bm25 + 0.4 * sim + 0.1 * tag_overlap + boosts


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(req: RetrieveRequest) -> RetrieveResponse:
    q = (req.question or "").strip()
    if not q:
        return RetrieveResponse(chunks=[], graph=GraphContext(nodes=[], edges=[]), designations=[])

    # Spatial tags to bias scoring
    desig_tags = _spatial_tags(req.site_geom.dict() if req.site_geom else None)

    chunks: List[ChunkItem] = []
    q_emb = get_embedding(q)

    # Try DB-backed hybrid search
    try:
        sql = """
            SELECT pp.id, p.doc_id, p.title, pp.para_ref, pp.text, pp.page,
                   ts_rank_cd(pp.tsv, plainto_tsquery('english', %s)) AS bm25,
                   (1 - (pp.embedding <=> %s::vector)) AS sim
            FROM policy_para pp
            JOIN policy p ON p.id = pp.policy_id
            WHERE (pp.tsv @@ plainto_tsquery('english', %s)) OR (pp.embedding IS NOT NULL)
            ORDER BY (0.5*COALESCE(ts_rank_cd(pp.tsv, plainto_tsquery('english', %s)),0) +
                      0.4*COALESCE((1 - (pp.embedding <=> %s::vector)),0)) DESC
            LIMIT %s
        """
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (q, to_vector(q_emb), q, q, to_vector(q_emb), req.top_k))
                rows = cur.fetchall()
        for rid, policy_id, title, pref, text, page, bm25, sim in rows:
            # tag_overlap heuristic: if clause mentions any designation token
            tag_overlap = 0.0
            low = text.lower()
            if desig_tags:
                hits = sum(1 for t in desig_tags if t.split(":")[-1].lower() in low)
                tag_overlap = min(1.0, hits / 3.0)
            score = _score_formula(float(bm25 or 0.0), float(sim or 0.0), tag_overlap)
            chunks.append(ChunkItem(
                chunk_id=str(rid),
                policy_id=str(policy_id),
                policy_title=title,
                para_ref=pref,
                text=text,
                page=page,
                score=score,
                bm25=float(bm25 or 0.0),
                sim=float(sim or 0.0),
                tags=desig_tags[:10] or None,
            ))
    except Exception:
        # Fixture-only fallback: scan small JSONL
        fp = Path("/home/tjm/code/demo/fixtures/lpa_demo/policy_paras.jsonl")
        if fp.exists():
            for line in fp.read_text().splitlines():
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                text = rec.get("text", "")
                if not text:
                    continue
                bm25 = 1.0 if any(tok in text.lower() for tok in q.lower().split()) else 0.0
                sim = bm25  # naive proxy
                tag_overlap = 0.0
                if desig_tags:
                    hits = sum(1 for t in desig_tags if t.split(":")[-1].lower() in text.lower())
                    tag_overlap = min(1.0, hits / 3.0)
                score = _score_formula(bm25, sim, tag_overlap)
                chunks.append(ChunkItem(
                    chunk_id=f"{rec.get('doc_id')}:{rec.get('para_ref')}",
                    policy_id=rec.get("doc_id"),
                    policy_title=rec.get("doc_id"),
                    para_ref=rec.get("para_ref"),
                    text=text,
                    page=rec.get("page"),
                    score=score,
                    bm25=bm25,
                    sim=sim,
                    tags=desig_tags[:10] or None,
                ))
        # sort and trim
        chunks.sort(key=lambda c: c.score, reverse=True)
        chunks = chunks[: req.top_k]

    # KG context based on top policies
    top_policy_ids = [c.policy_id for c in chunks if c.policy_id]
    graph = _kg_neighbors(top_policy_ids)

    return RetrieveResponse(
        chunks=chunks,
        graph=graph,
        designations=desig_tags or None,
    )
