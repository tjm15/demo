"""Policy search service - hybrid text + vector search backed by Postgres.

Implements:
- POST /search: hybrid search over policy paragraphs
- GET /{policy_id}/graph: return references and tests from DB
"""
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db import get_conn, to_vector
from modules.embedding import get_embedding

router = APIRouter()

class PolicyHit(BaseModel):
    id: str
    title: str
    text: str
    relevance: float
    source: str

class PolicySearchRequest(BaseModel):
    query: str
    limit: int = 10

class PolicyGraph(BaseModel):
    policy_id: str
    references: List[str]
    referenced_by: List[str]
    exceptions: List[str]
    tests: List[dict]

@router.post("/search", response_model=List[PolicyHit])
async def search_policies(req: PolicySearchRequest):
    """Hybrid search using full-text rank and vector similarity."""
    q = req.query.strip()
    if not q:
        return []

    hits: List[PolicyHit] = []
    q_emb = get_embedding(q)
    sql = """
        SELECT p.doc_id,
               p.title,
               pp.text,
               ts_rank_cd(pp.tsv, plainto_tsquery('english', %s)) AS rank_txt,
               (1 - (pp.embedding <=> %s::vector)) AS rank_vec,
               (0.6 * COALESCE(ts_rank_cd(pp.tsv, plainto_tsquery('english', %s)), 0) +
                0.4 * COALESCE(1 - (pp.embedding <=> %s::vector), 0)) AS score
        FROM policy_para pp
        JOIN policy p ON p.id = pp.policy_id
        WHERE (pp.tsv @@ plainto_tsquery('english', %s)) OR (pp.embedding IS NOT NULL)
        ORDER BY score DESC
        LIMIT %s
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (q, to_vector(q_emb), q, to_vector(q_emb), q, req.limit))
                for doc_id, title, text, rank_txt, rank_vec, score in cur.fetchall():
                    hits.append(PolicyHit(
                        id=str(doc_id),
                        title=title,
                        text=text,
                        relevance=float(score or 0.0),
                        source=title,
                    ))
    except Exception:
        # Fallback to text-only search
        sql2 = """
            SELECT p.doc_id, p.title, pp.text, ts_rank_cd(pp.tsv, plainto_tsquery('english', %s)) AS rank
            FROM policy_para pp
            JOIN policy p ON p.id = pp.policy_id
            WHERE pp.tsv @@ plainto_tsquery('english', %s)
            ORDER BY rank DESC
            LIMIT %s
        """
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql2, (q, q, req.limit))
                for doc_id, title, text, rank in cur.fetchall():
                    hits.append(PolicyHit(id=str(doc_id), title=title, text=text, relevance=float(rank or 0.0), source=title))
    return hits

@router.get("/{policy_id}/graph", response_model=PolicyGraph)
async def get_policy_graph(policy_id: str):
    """Get policy relationships and tests from DB. Accepts doc_id or numeric id."""
    # Resolve to numeric id
    policy_pk = None
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM policy WHERE doc_id = %s", (policy_id,))
            row = cur.fetchone()
            if row:
                policy_pk = row[0]
            else:
                try:
                    as_int = int(policy_id)
                except ValueError:
                    as_int = None
                if as_int is not None:
                    cur.execute("SELECT id FROM policy WHERE id = %s", (as_int,))
                    row2 = cur.fetchone()
                    if row2:
                        policy_pk = row2[0]
    if policy_pk is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    references: List[str] = []
    referenced_by: List[str] = []
    exceptions: List[str] = []
    tests: List[dict] = []

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p2.doc_id
                FROM policy_rel r
                JOIN policy p2 ON p2.id = r.to_policy_id
                WHERE r.from_policy_id = %s AND r.rel_type = 'reference'
                """,
                (policy_pk,),
            )
            references = [r[0] for r in cur.fetchall()]

            cur.execute(
                """
                SELECT p1.doc_id
                FROM policy_rel r
                JOIN policy p1 ON p1.id = r.from_policy_id
                WHERE r.to_policy_id = %s AND r.rel_type = 'reference'
                """,
                (policy_pk,),
            )
            referenced_by = [r[0] for r in cur.fetchall()]

            cur.execute("SELECT test_name, operator, value, unit FROM policy_test WHERE policy_id = %s", (policy_pk,))
            for name, op, val, unit in cur.fetchall():
                tests.append({
                    "name": name,
                    "operator": op,
                    "value": float(val) if val is not None else None,
                    "unit": unit,
                })

    return PolicyGraph(
        policy_id=str(policy_pk),
        references=references,
        referenced_by=referenced_by,
        exceptions=exceptions,
        tests=tests,
    )

@router.get("/{policy_id}/graph", response_model=PolicyGraph)
async def get_policy_graph(policy_id: str):
    """Get policy relationships and tests from DB.
    Accepts either numeric ID or doc_id.
    """
    # Resolve to numeric id
    policy_pk = None
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Try doc_id match first
            cur.execute("SELECT id FROM policy WHERE doc_id = %s", (policy_id,))
            row = cur.fetchone()
            if row:
                policy_pk = row[0]
            else:
                # Try integer cast
                try:
                    as_int = int(policy_id)
                except ValueError:
                    pass
                else:
                    cur.execute("SELECT id FROM policy WHERE id = %s", (as_int,))
                    row2 = cur.fetchone()
                    if row2:
                        policy_pk = row2[0]
    if policy_pk is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    references: List[str] = []
    referenced_by: List[str] = []
    exceptions: List[str] = []
    tests: List[dict] = []

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p2.doc_id
                FROM policy_rel r
                JOIN policy p2 ON p2.id = r.to_policy_id
                WHERE r.from_policy_id = %s AND r.rel_type = 'reference'
            """, (policy_pk,))
            references = [r[0] for r in cur.fetchall()]

            cur.execute("""
                SELECT p1.doc_id
                FROM policy_rel r
                JOIN policy p1 ON p1.id = r.from_policy_id
                WHERE r.to_policy_id = %s AND r.rel_type = 'reference'
            """, (policy_pk,))
            referenced_by = [r[0] for r in cur.fetchall()]

            cur.execute("SELECT test_name, operator, value, unit FROM policy_test WHERE policy_id = %s", (policy_pk,))
            for name, op, val, unit in cur.fetchall():
                tests.append({"name": name, "operator": op, "value": float(val) if val is not None else None, "unit": unit})

    return PolicyGraph(
        policy_id=str(policy_pk),
        references=references,
        referenced_by=referenced_by,
        exceptions=exceptions,
        tests=tests,
    )
