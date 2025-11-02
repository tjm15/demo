"""
Evidence service - manage evidence base items, versions, and retrieval
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from db import get_conn
import hashlib

router = APIRouter()

# ============================================================================
# Request/Response Models
# ============================================================================

class EvidenceSearchRequest(BaseModel):
    q: Optional[str] = None
    topic: Optional[List[str]] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    type: Optional[str] = None
    status: Optional[List[str]] = None
    scope: str = "db"  # 'db', 'cache', 'live'
    linked_policy_id: Optional[int] = None
    spatial_only: bool = False
    limit: int = 50

class EvidenceItem(BaseModel):
    id: int
    title: str
    type: str
    topic_tags: List[str]
    geographic_scope: Optional[str]
    author: Optional[str]
    publisher: Optional[str]
    year: Optional[int]
    source_type: str
    spatial_layer_ref: Optional[int]
    key_findings: Optional[str]
    status: str
    reliability_flags: Dict[str, Any]
    notes: Optional[str]
    version_count: int
    latest_version: Optional[int]
    created_at: datetime
    updated_at: datetime

class EvidenceVersion(BaseModel):
    id: int
    evidence_id: int
    version_number: int
    cas_hash: str
    source_url: Optional[str]
    etag: Optional[str]
    last_modified: Optional[datetime]
    file_size: Optional[int]
    mime_type: Optional[str]
    fetched_at: datetime
    license: Optional[str]
    robots_allowed: bool

class EvidencePolicyLink(BaseModel):
    evidence_id: int
    policy_id: int
    rationale: Optional[str]
    strength: str

class EvidenceDetail(BaseModel):
    item: EvidenceItem
    versions: List[EvidenceVersion]
    policy_links: List[EvidencePolicyLink]
    layer_ids: List[int]

class LinkPolicyRequest(BaseModel):
    policy_id: int
    rationale: Optional[str] = None
    strength: str = "supporting"

class FetchUrlRequest(BaseModel):
    url: str
    title: Optional[str] = None
    type: str
    topic_tags: List[str] = []

# ============================================================================
# Search & Filter
# ============================================================================

@router.post("/search", response_model=List[EvidenceItem])
async def search_evidence(req: EvidenceSearchRequest):
    """
    Search evidence items with filters.
    Supports full-text search, topic filtering, year range, type, status, etc.
    """
    query_parts = ["SELECT DISTINCT e.* FROM evidence e"]
    where_clauses = []
    params = []
    param_idx = 1

    # Version count subquery
    query_parts.append("""
        LEFT JOIN (
            SELECT evidence_id, COUNT(*) as version_count, MAX(version_number) as latest_version
            FROM evidence_version
            GROUP BY evidence_id
        ) ev ON ev.evidence_id = e.id
    """)

    # Text search
    if req.q:
        query_parts.append("LEFT JOIN evidence_chunk ec ON ec.evidence_version_id IN (SELECT id FROM evidence_version WHERE evidence_id = e.id)")
        # Use three parameters for the three places where q is used
        where_clauses.append(f"(e.title ILIKE ${param_idx} OR e.key_findings ILIKE ${param_idx+1} OR ec.tsv @@ plainto_tsquery('english', ${param_idx+2}))")
        params.extend([f"%{req.q}%", f"%{req.q}%", req.q])
        param_idx += 3

    # Topic filter
    if req.topic:
        where_clauses.append(f"e.topic_tags && ${param_idx}")
        params.append(req.topic)
        param_idx += 1

    # Year range
    if req.year_min:
        where_clauses.append(f"e.year >= ${param_idx}")
        params.append(req.year_min)
        param_idx += 1
    if req.year_max:
        where_clauses.append(f"e.year <= ${param_idx}")
        params.append(req.year_max)
        param_idx += 1

    # Type filter
    if req.type:
        where_clauses.append(f"e.type = ${param_idx}")
        params.append(req.type)
        param_idx += 1

    # Status filter
    if req.status:
        where_clauses.append(f"e.status = ANY(${param_idx})")
        params.append(req.status)
        param_idx += 1

    # Spatial only
    if req.spatial_only:
        where_clauses.append("e.spatial_layer_ref IS NOT NULL")

    # Linked to specific policy
    if req.linked_policy_id:
        query_parts.append("INNER JOIN evidence_policy_link epl ON epl.evidence_id = e.id")
        where_clauses.append(f"epl.policy_id = ${param_idx}")
        params.append(req.linked_policy_id)
        param_idx += 1

    # Build query
    if where_clauses:
        query_parts.append("WHERE " + " AND ".join(where_clauses))

    query_parts.append(f"ORDER BY e.updated_at DESC LIMIT ${param_idx}")
    params.append(req.limit)

    query = " ".join(query_parts)

    # Execute
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Replace $1, $2 with %s for psycopg
            query_pg = query
            for i in range(len(params), 0, -1):
                query_pg = query_pg.replace(f"${i}", "%s")
            
            cur.execute(query_pg, params)
            rows = cur.fetchall()
            
            results = []
            for row in rows:
                results.append(EvidenceItem(
                    id=row[0],
                    title=row[1],
                    type=row[2],
                    topic_tags=row[3] or [],
                    geographic_scope=row[4],
                    author=row[5],
                    publisher=row[6],
                    year=row[7],
                    source_type=row[8],
                    spatial_layer_ref=row[9],
                    key_findings=row[10],
                    status=row[11],
                    reliability_flags=row[12] or {},
                    notes=row[13],
                    version_count=0,  # TODO: join
                    latest_version=None,
                    created_at=row[14],
                    updated_at=row[15]
                ))
            
            return results

# ============================================================================
# Detail View
# ============================================================================

@router.get("/{evidence_id}", response_model=EvidenceDetail)
async def get_evidence_detail(evidence_id: int):
    """
    Get full evidence record with versions, policy links, and layer references.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Main item
            cur.execute("SELECT * FROM evidence WHERE id = %s", (evidence_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Evidence not found")
            
            item = EvidenceItem(
                id=row[0],
                title=row[1],
                type=row[2],
                topic_tags=row[3] or [],
                geographic_scope=row[4],
                author=row[5],
                publisher=row[6],
                year=row[7],
                source_type=row[8],
                spatial_layer_ref=row[9],
                key_findings=row[10],
                status=row[11],
                reliability_flags=row[12] or {},
                notes=row[13],
                version_count=0,
                latest_version=None,
                created_at=row[14],
                updated_at=row[15]
            )

            # Versions
            cur.execute("""
                SELECT id, evidence_id, version_number, cas_hash, source_url, etag, 
                       last_modified, file_size, mime_type, fetched_at, license, robots_allowed
                FROM evidence_version
                WHERE evidence_id = %s
                ORDER BY version_number DESC
            """, (evidence_id,))
            versions = [
                EvidenceVersion(
                    id=v[0], evidence_id=v[1], version_number=v[2], cas_hash=v[3],
                    source_url=v[4], etag=v[5], last_modified=v[6], file_size=v[7],
                    mime_type=v[8], fetched_at=v[9], license=v[10], robots_allowed=v[11]
                )
                for v in cur.fetchall()
            ]

            # Policy links
            cur.execute("""
                SELECT evidence_id, policy_id, rationale, strength
                FROM evidence_policy_link
                WHERE evidence_id = %s
            """, (evidence_id,))
            policy_links = [
                EvidencePolicyLink(evidence_id=p[0], policy_id=p[1], rationale=p[2], strength=p[3])
                for p in cur.fetchall()
            ]

            # Layer IDs
            cur.execute("SELECT layer_id FROM evidence_layer WHERE evidence_id = %s", (evidence_id,))
            layer_ids = [row[0] for row in cur.fetchall()]

            return EvidenceDetail(
                item=item,
                versions=versions,
                policy_links=policy_links,
                layer_ids=layer_ids
            )

# ============================================================================
# Link to Policy
# ============================================================================

@router.post("/{evidence_id}/link-policy")
async def link_to_policy(evidence_id: int, req: LinkPolicyRequest):
    """
    Link evidence item to a policy with rationale and strength.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO evidence_policy_link (evidence_id, policy_id, rationale, strength)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (evidence_id, policy_id) 
                DO UPDATE SET rationale = EXCLUDED.rationale, strength = EXCLUDED.strength
                RETURNING id
            """, (evidence_id, req.policy_id, req.rationale, req.strength))
            conn.commit()
            link_id = cur.fetchone()[0]
            return {"id": link_id, "evidence_id": evidence_id, "policy_id": req.policy_id}

# ============================================================================
# Dependency Graph
# ============================================================================

@router.get("/graph/dependencies")
async def get_dependency_graph(policy_id: Optional[int] = None, evidence_id: Optional[int] = None):
    """
    Return evidence ↔ policy dependency graph.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            where = []
            params = []
            if policy_id:
                where.append("epl.policy_id = %s")
                params.append(policy_id)
            if evidence_id:
                where.append("epl.evidence_id = %s")
                params.append(evidence_id)
            
            query = """
                SELECT e.id, e.title, e.type, p.id, p.title, epl.strength, epl.rationale
                FROM evidence_policy_link epl
                JOIN evidence e ON e.id = epl.evidence_id
                JOIN policy p ON p.id = epl.policy_id
            """
            if where:
                query += " WHERE " + " AND ".join(where)
            
            cur.execute(query, params)
            rows = cur.fetchall()
            
            nodes = []
            edges = []
            seen_evidence = set()
            seen_policy = set()
            
            for row in rows:
                e_id, e_title, e_type, p_id, p_title, strength, rationale = row
                if e_id not in seen_evidence:
                    nodes.append({"id": f"e{e_id}", "label": e_title, "type": "evidence", "subtype": e_type})
                    seen_evidence.add(e_id)
                if p_id not in seen_policy:
                    nodes.append({"id": f"p{p_id}", "label": p_title, "type": "policy"})
                    seen_policy.add(p_id)
                edges.append({
                    "from": f"e{e_id}",
                    "to": f"p{p_id}",
                    "strength": strength,
                    "rationale": rationale
                })
            
            return {"nodes": nodes, "edges": edges}

# ============================================================================
# Gap Analysis
# ============================================================================

@router.get("/gaps")
async def evidence_gaps():
    """
    Identify policies with weak/stale/no evidence.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Policies with no evidence
            cur.execute("""
                SELECT p.id, p.title
                FROM policy p
                LEFT JOIN evidence_policy_link epl ON epl.policy_id = p.id
                WHERE epl.id IS NULL
            """)
            no_evidence = [{"policy_id": row[0], "title": row[1]} for row in cur.fetchall()]

            # Policies with only stale evidence (>5 years old)
            cur.execute("""
                SELECT p.id, p.title, MAX(e.year) as latest_year
                FROM policy p
                JOIN evidence_policy_link epl ON epl.policy_id = p.id
                JOIN evidence e ON e.id = epl.evidence_id
                GROUP BY p.id, p.title
                HAVING MAX(e.year) < EXTRACT(YEAR FROM NOW()) - 5
            """)
            stale_evidence = [{"policy_id": row[0], "title": row[1], "latest_year": row[2]} for row in cur.fetchall()]

            # Policies with only weak links
            cur.execute("""
                SELECT p.id, p.title, COUNT(*) as link_count
                FROM policy p
                JOIN evidence_policy_link epl ON epl.policy_id = p.id
                WHERE epl.strength = 'tangential'
                GROUP BY p.id, p.title
                HAVING COUNT(*) = (
                    SELECT COUNT(*) FROM evidence_policy_link WHERE policy_id = p.id
                )
            """)
            weak_links = [{"policy_id": row[0], "title": row[1], "link_count": row[2]} for row in cur.fetchall()]

            return {
                "no_evidence": no_evidence,
                "stale_evidence": stale_evidence,
                "weak_links_only": weak_links
            }
