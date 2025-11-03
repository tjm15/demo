"""
Evidence service - manage evidence base items, versions, and retrieval
Enhanced with vector search, semantic retrieval, and analysis features
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from db import get_conn
from embedding import embed
import hashlib
import json

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
    use_semantic: bool = True  # Enable vector search by default

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
    relevance_score: Optional[float] = None  # For semantic search results

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
    related_evidence: List[int] = []  # IDs of related evidence items

class LinkPolicyRequest(BaseModel):
    policy_id: int
    rationale: Optional[str] = None
    strength: str = "supporting"

class FetchUrlRequest(BaseModel):
    url: str
    title: Optional[str] = None
    type: str
    topic_tags: List[str] = []

class VersionDiffResponse(BaseModel):
    version_a: EvidenceVersion
    version_b: EvidenceVersion
    key_findings_diff: Dict[str, Any]

class RelatedEvidenceResponse(BaseModel):
    evidence_id: int
    related: List[EvidenceItem]

# ============================================================================
# Semantic / Vector Search
# ============================================================================

@router.post("/search_semantic", response_model=List[EvidenceItem])
async def search_semantic(req: EvidenceSearchRequest):
    """
    Semantic search using pgvector embeddings on evidence chunks.
    Combines vector similarity with metadata filters for hybrid search.
    """
    if not req.q:
        return []
    
    # Generate query embedding
    query_vec = embed(req.q)
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Build semantic search query
            query_parts = ["""
                SELECT DISTINCT 
                    e.*,
                    MIN(ec.embedding <=> %s::vector) as similarity,
                    COUNT(DISTINCT ev.id) as version_count,
                    MAX(ev.version_number) as latest_version
                FROM evidence e
                JOIN evidence_version ev ON ev.evidence_id = e.id
                JOIN evidence_chunk ec ON ec.evidence_version_id = ev.id
            """]
            
            where_clauses = ["ec.embedding <=> %s::vector < 0.6"]  # Similarity threshold
            params = [query_vec, query_vec]
            
            # Add metadata filters
            if req.topic:
                where_clauses.append("e.topic_tags && %s")
                params.append(req.topic)
            
            if req.year_min:
                where_clauses.append("e.year >= %s")
                params.append(req.year_min)
            
            if req.year_max:
                where_clauses.append("e.year <= %s")
                params.append(req.year_max)
            
            if req.type:
                where_clauses.append("e.type = %s")
                params.append(req.type)
            
            if req.status:
                where_clauses.append("e.status = ANY(%s)")
                params.append(req.status)
            
            if req.spatial_only:
                where_clauses.append("e.spatial_layer_ref IS NOT NULL")
            
            if req.linked_policy_id:
                query_parts.append("JOIN evidence_policy_link epl ON epl.evidence_id = e.id")
                where_clauses.append("epl.policy_id = %s")
                params.append(req.linked_policy_id)
            
            # Build final query
            query_parts.append("WHERE " + " AND ".join(where_clauses))
            query_parts.append("GROUP BY e.id")
            query_parts.append("ORDER BY similarity ASC")
            query_parts.append("LIMIT %s")
            params.append(req.limit)
            
            query = " ".join(query_parts)
            
            try:
                cur.execute(query, params)
                rows = cur.fetchall()
                
                results = []
                for row in rows:
                    similarity = row[16] if len(row) > 16 else 0.0
                    version_count = row[17] if len(row) > 17 else 0
                    latest_version = row[18] if len(row) > 18 else None
                    
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
                        version_count=version_count,
                        latest_version=latest_version,
                        created_at=row[14],
                        updated_at=row[15],
                        relevance_score=1.0 - float(similarity)  # Convert distance to similarity
                    ))
                
                return results
            except Exception as e:
                # Fallback to text search if vector search fails
                print(f"Semantic search failed, falling back to text search: {e}")
                return await search_evidence(req)

# ============================================================================
# Related Evidence Finder
# ============================================================================

@router.get("/{evidence_id}/related", response_model=RelatedEvidenceResponse)
async def get_related_evidence(evidence_id: int, limit: int = 5):
    """
    Find evidence items related to the given one using semantic similarity.
    Based on title, key findings, and topic overlap.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Get source evidence
            cur.execute("""
                SELECT title, key_findings, topic_tags, type
                FROM evidence
                WHERE id = %s
            """, (evidence_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Evidence not found")
            
            title, key_findings, topic_tags, evidence_type = row
            query_text = f"{title} {key_findings or ''}"
            query_vec = embed(query_text)
            
            # Find similar evidence using vector search
            cur.execute("""
                SELECT DISTINCT 
                    e.*,
                    MIN(ec.embedding <=> %s::vector) as similarity,
                    COUNT(DISTINCT ev.id) as version_count,
                    MAX(ev.version_number) as latest_version
                FROM evidence e
                JOIN evidence_version ev ON ev.evidence_id = e.id
                JOIN evidence_chunk ec ON ec.evidence_version_id = ev.id
                WHERE e.id != %s
                    AND (
                        e.topic_tags && %s  -- Overlapping topics
                        OR e.type = %s      -- Same evidence type
                        OR ec.embedding <=> %s::vector < 0.5
                    )
                GROUP BY e.id
                ORDER BY similarity ASC
                LIMIT %s
            """, (query_vec, evidence_id, topic_tags or [], evidence_type, query_vec, limit))
            
            rows = cur.fetchall()
            related = []
            for row in rows:
                similarity = row[16] if len(row) > 16 else 0.0
                version_count = row[17] if len(row) > 17 else 0
                latest_version = row[18] if len(row) > 18 else None
                
                related.append(EvidenceItem(
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
                    version_count=version_count,
                    latest_version=latest_version,
                    created_at=row[14],
                    updated_at=row[15],
                    relevance_score=1.0 - float(similarity)
                ))
            
            return RelatedEvidenceResponse(
                evidence_id=evidence_id,
                related=related
            )

# ============================================================================
# Version Diff
# ============================================================================

@router.get("/{evidence_id}/versions/diff", response_model=VersionDiffResponse)
async def diff_versions(evidence_id: int, version_a: int, version_b: int):
    """
    Compare key findings between two versions of an evidence item.
    Returns structured diff highlighting changes.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Get both versions
            cur.execute("""
                SELECT id, evidence_id, version_number, cas_hash, source_url,
                       etag, last_modified, file_size, mime_type, fetched_at,
                       license, robots_allowed
                FROM evidence_version
                WHERE evidence_id = %s AND version_number IN (%s, %s)
                ORDER BY version_number
            """, (evidence_id, version_a, version_b))
            
            rows = cur.fetchall()
            if len(rows) != 2:
                raise HTTPException(status_code=404, detail="One or both versions not found")
            
            v_a = EvidenceVersion(
                id=rows[0][0], evidence_id=rows[0][1], version_number=rows[0][2],
                cas_hash=rows[0][3], source_url=rows[0][4], etag=rows[0][5],
                last_modified=rows[0][6], file_size=rows[0][7], mime_type=rows[0][8],
                fetched_at=rows[0][9], license=rows[0][10], robots_allowed=rows[0][11]
            )
            
            v_b = EvidenceVersion(
                id=rows[1][0], evidence_id=rows[1][1], version_number=rows[1][2],
                cas_hash=rows[1][3], source_url=rows[1][4], etag=rows[1][5],
                last_modified=rows[1][6], file_size=rows[1][7], mime_type=rows[1][8],
                fetched_at=rows[1][9], license=rows[1][10], robots_allowed=rows[1][11]
            )
            
            # Get key findings for the evidence item (only one set, but track version info in notes)
            cur.execute("SELECT key_findings FROM evidence WHERE id = %s", (evidence_id,))
            key_findings = cur.fetchone()[0] if cur.rowcount > 0 else ""
            
            # For now, return basic diff structure
            # In production, parse key findings and do structured diff
            diff = {
                "summary": f"Comparing version {version_a} to version {version_b}",
                "changes_detected": v_a.cas_hash != v_b.cas_hash,
                "key_findings_current": key_findings,
                "note": "Detailed text diff requires parsing key_findings structure"
            }
            
            return VersionDiffResponse(
                version_a=v_a,
                version_b=v_b,
                key_findings_diff=diff
            )

# ============================================================================
# Spatial Layer Metadata
# ============================================================================

@router.get("/{evidence_id}/spatial")
async def get_spatial_metadata(evidence_id: int):
    """
    Return PostGIS layer metadata for evidence with spatial components.
    Includes bbox, SRID, feature count, and geometry types.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Check if evidence has spatial layers
            cur.execute("""
                SELECT l.id, l.name, l.source, l.srid,
                       ST_AsText(ST_Extent(lg.geom)) as bbox,
                       COUNT(lg.id) as feature_count,
                       ST_GeometryType(lg.geom) as geom_type
                FROM evidence e
                JOIN evidence_layer el ON el.evidence_id = e.id
                JOIN layer l ON l.id = el.layer_id
                LEFT JOIN layer_geom lg ON lg.layer_id = l.id
                WHERE e.id = %s
                GROUP BY l.id, l.name, l.source, l.srid, lg.geom
            """, (evidence_id,))
            
            rows = cur.fetchall()
            if not rows:
                return {"evidence_id": evidence_id, "layers": []}
            
            layers = []
            for row in rows:
                layers.append({
                    "layer_id": row[0],
                    "name": row[1],
                    "source": row[2],
                    "srid": row[3],
                    "bbox_wkt": row[4],
                    "feature_count": row[5],
                    "geometry_type": row[6]
                })
            
            return {
                "evidence_id": evidence_id,
                "layers": layers
            }

# ============================================================================
# Enhanced Search & Filter (with fallback)
# ============================================================================

# ============================================================================
# Gap Analysis (MUST come before /{evidence_id} route)
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

# ============================================================================
# Dependency Graph (MUST come before /{evidence_id} route)
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
@router.post("/search", response_model=List[EvidenceItem])
async def search_evidence(req: EvidenceSearchRequest):
    """
    Search evidence items with filters.
    Uses semantic search if query text provided and use_semantic=True,
    otherwise falls back to full-text and metadata filtering.
    """
    # Use semantic search for text queries
    if req.q and req.use_semantic:
        try:
            return await search_semantic(req)
        except Exception as e:
            print(f"Semantic search failed, using text search: {e}")
            # Fall through to text search
    
    query_parts = ["SELECT DISTINCT e.*, 0 as version_count, 0 as latest_version FROM evidence e"]
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

    # Text search using full-text
    if req.q:
        query_parts.append("LEFT JOIN evidence_chunk ec ON ec.evidence_version_id IN (SELECT id FROM evidence_version WHERE evidence_id = e.id)")
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
                # Handle version count from join
                version_count = row[17] if len(row) > 17 and row[17] is not None else 0
                latest_version = row[18] if len(row) > 18 else None
                
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
                    version_count=version_count,
                    latest_version=latest_version,
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
    Get full evidence record with versions, policy links, layer references,
    and related evidence items.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Main item
            cur.execute("""
                SELECT e.*, 
                       COUNT(DISTINCT ev.id) as version_count,
                       MAX(ev.version_number) as latest_version
                FROM evidence e
                LEFT JOIN evidence_version ev ON ev.evidence_id = e.id
                WHERE e.id = %s
                GROUP BY e.id
            """, (evidence_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Evidence not found")
            
            version_count = row[16] if len(row) > 16 else 0
            latest_version = row[17] if len(row) > 17 else None
            
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
                version_count=version_count,
                latest_version=latest_version,
                created_at=row[14],
                updated_at=row[15]
            )
            
            # Versions for the evidence item
            cur.execute("""
                SELECT id, evidence_id, version_number, cas_hash, source_url,
                       etag, last_modified, file_size, mime_type, fetched_at,
                       license, robots_allowed
                FROM evidence_version
                WHERE evidence_id = %s
                ORDER BY version_number DESC
            """, (evidence_id,))
            vrows = cur.fetchall()
            versions = [
                EvidenceVersion(
                    id=v[0], evidence_id=v[1], version_number=v[2],
                    cas_hash=v[3], source_url=v[4], etag=v[5],
                    last_modified=v[6], file_size=v[7], mime_type=v[8],
                    fetched_at=v[9], license=v[10], robots_allowed=v[11]
                ) for v in vrows
            ]

            # Policy links
            cur.execute("""
                SELECT evidence_id, policy_id, rationale, strength
                FROM evidence_policy_link
                WHERE evidence_id = %s
            """, (evidence_id,))
            plinks = [
                EvidencePolicyLink(
                    evidence_id=pr[0], policy_id=pr[1], rationale=pr[2], strength=pr[3]
                ) for pr in cur.fetchall()
            ]

            # Layer ids
            cur.execute("""
                SELECT layer_id FROM evidence_layer WHERE evidence_id = %s
            """, (evidence_id,))
            layer_ids = [r[0] for r in cur.fetchall()]

            # Related evidence IDs (by simple semantic + topic overlap)
            # Reuse vector similarity but return IDs only
            related_ids: List[int] = []
            try:
                # Build a lightweight vector based on title + key findings
                qtext = f"{item.title} {item.key_findings or ''}"
                qvec = embed(qtext)
                cur.execute("""
                    SELECT e.id
                    FROM evidence e
                    JOIN evidence_version ev ON ev.evidence_id = e.id
                    JOIN evidence_chunk ec ON ec.evidence_version_id = ev.id
                    WHERE e.id != %s
                    GROUP BY e.id
                    ORDER BY MIN(ec.embedding <=> %s::vector) ASC
                    LIMIT 5
                """, (evidence_id, qvec))
                related_ids = [r[0] for r in cur.fetchall()]
            except Exception:
                # Fallback: topic overlap
                cur.execute("""
                    SELECT id FROM evidence
                    WHERE id != %s AND topic_tags && %s
                    LIMIT 5
                """, (evidence_id, item.topic_tags))
                related_ids = [r[0] for r in cur.fetchall()]

            return EvidenceDetail(
                item=item,
                versions=versions,
                policy_links=plinks,
                layer_ids=layer_ids,
                related_evidence=related_ids
            )

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
