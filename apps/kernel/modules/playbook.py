"""Playbook execution - orchestrates reasoning flow using live services (DB)."""
import asyncio
from typing import AsyncGenerator, Dict, Any, List
from pathlib import Path
from datetime import datetime

from modules.context import ContextPack
from modules.trace import TraceEntry, write_trace
from modules import llm
from modules import proxy_client
from modules.panel_planner import plan_panels
from modules.panel_dispatcher import dispatch_panel
from modules.reasoning_executor import run_auto_actions, extract_actions
from db import get_conn

# Module-specific allowed domains for citations
ALLOWED_BY_MODULE = {
    "dm": ["gov.uk", "london.gov.uk", "planninginspectorate.gov.uk"],
    "policy": ["gov.uk", "london.gov.uk", "planninginspectorate.gov.uk"],
    "strategy": ["gov.uk", "london.gov.uk"],
    "vision": ["gov.uk", "london.gov.uk"],
    "feedback": ["gov.uk", "london.gov.uk"],
    "evidence": ["gov.uk", "london.gov.uk", "planningportal.co.uk"]
}

from typing import Union
from datetime import date


def _sanitize_for_json(obj: Any) -> Any:
    """Recursively convert objects into JSON-serializable forms.
    Handles datetime/date, sets/tuples, and pydantic-like models with model_dump.
    """
    try:
        from pydantic import BaseModel  # local import to avoid hard dep at import time
    except Exception:
        BaseModel = None  # type: ignore

    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize_for_json(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    if BaseModel and isinstance(obj, BaseModel):  # type: ignore[arg-type]
        try:
            return obj.model_dump()
        except Exception:
            pass
    # Fallback to string
    try:
        return str(obj)
    except Exception:
        return "<unserializable>"


async def execute_playbook(context: ContextPack, trace_path: Path) -> AsyncGenerator[Dict[str, Any], None]:
    """Execute reasoning playbook for given module."""
    
    print(f"[Playbook] Starting execute_playbook for module={context.module}")
    
    # Phase 1: Planning
    try:
        yield {
            "type": "intent",
            "data": _sanitize_for_json({
                "action": "init_workspace",
                "module": context.module,
                "message": f"Initializing {context.module.upper()} module workspace..."
            })
        }
        print(f"[Playbook] Yielded init_workspace intent")
    except Exception as e:
        print(f"[Playbook] Failed to yield init_workspace: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    await asyncio.sleep(0.1)
    
    # Phase 2: Retrieval
    await write_trace(trace_path, TraceEntry(
        t=datetime.utcnow().isoformat(),
        step="retrieve",
        module=context.module,
        input={"prompt": context.prompt}
    ))

    # Try on-demand web retrieval via proxy within per-run cap
    citations: List[Dict[str, Any]] = []
    web_limit = context.get_web_fetch_limit()
    if web_limit > 0:
        try:
            results = await proxy_client.proxy_search(context.prompt)
            for r in results:
                if len(citations) >= web_limit:
                    break
                url = r.get("url")
                if not url:
                    continue
                dom = proxy_client.domain_from_url(url)
                if not _domain_allowed(dom, context.module):
                    await write_trace(trace_path, TraceEntry(
                        t=datetime.utcnow().isoformat(),
                        step="citation_suppressed",
                        module=context.module,
                        input={"url": url, "domain": dom},
                        output={"reason": "domain not allowed for module"}
                    ))
                    continue
                dl = await proxy_client.proxy_download(url)
                cache_key = dl.get("cache_key")
                if not cache_key:
                    continue
                ex = await proxy_client.proxy_extract(cache_key)
                paras = ex.get("paragraphs", [])
                snippet = (paras[0].get("text") if paras else r.get("snippet")) or ""
                citations.append({
                    "title": r.get("title") or dom,
                    "url": url,
                    "domain": dom,
                    "snippet": snippet[:240],
                })
        except Exception as e:
            await write_trace(trace_path, TraceEntry(
                t=datetime.utcnow().isoformat(),
                step="proxy_error",
                module=context.module,
                error=str(e)
            ))
    
    # Initial panel hint
    yield {
        "type": "intent",
        "data": _sanitize_for_json({
            "action": "show_panel",
            "panel": "evidence_snapshot" if context.module == "evidence" else "applicable_policies",
            "message": "Retrieving relevant data..."
        })
    }
    # For Evidence module, proactively emit Evidence Browser with initial results
    if context.module == "evidence":
        try:
            from modules.playbook import db_search_evidence as _dbse
            items_raw = _dbse(context.prompt or "", limit=50)
            # Sanitize the entire items list to ensure no datetime/date objects leak
            items = _sanitize_for_json(items_raw)
            print(f"[Playbook] Evidence browser items count: {len(items)}")
            payload = {
                "action": "show_panel",
                "panel": "evidence_browser",
                "data": {"items": items, "filters": {"topics": [], "scope": "db"}}
            }
            print(f"[Playbook] About to yield evidence_browser intent")
            yield {
                "type": "intent",
                "data": payload
            }
        except Exception as _e:
            print(f"[Playbook] Evidence browser emission failed: {_e}")
            import traceback
            traceback.print_exc()
            # Non-fatal; continue with planning
            pass
    await asyncio.sleep(0.1)
    
    # Phase 3: LLM-driven panel planning
    await write_trace(trace_path, TraceEntry(
        t=datetime.utcnow().isoformat(),
        step="plan_panels",
        module=context.module,
        input={"prompt": context.prompt}
    ))
    
    panel_plan = await plan_panels(context)
    
    await write_trace(trace_path, TraceEntry(
        t=datetime.utcnow().isoformat(),
        step="panel_plan",
        module=context.module,
        output={"panels": panel_plan}
    ))
    
    print(f"[Playbook] Panel plan for {context.module}: {panel_plan}")
    
    # Phase 3B: Execute panel plan
    for panel_name in panel_plan:
        try:
            panel_intent = await dispatch_panel(panel_name, context, citations)
            
            if panel_intent:
                # Ensure panel intent payload is serializable
                yield {"type": panel_intent.get("type"), "data": _sanitize_for_json(panel_intent.get("data"))}
                await asyncio.sleep(0.1)
                
                await write_trace(trace_path, TraceEntry(
                    t=datetime.utcnow().isoformat(),
                    step="emit_panel",
                    module=context.module,
                    output={"panel": panel_name}
                ))
        except Exception as e:
            print(f"[Playbook] Failed to dispatch panel {panel_name}: {e}")
            await write_trace(trace_path, TraceEntry(
                t=datetime.utcnow().isoformat(),
                step="panel_error",
                module=context.module,
                input={"panel": panel_name},
                error=str(e)
            ))
    
    # Phase 4: Streaming reasoning tokens (via LLM if available)
    sys_prompt = llm.build_system_prompt(context.module)
    usr_prompt = llm.build_user_prompt(context.module, context.prompt, context.site_data, context.proposal_data)
    stitched = f"SYSTEM:\n{sys_prompt}\n\nUSER:\n{usr_prompt}"

    print(f"[Playbook] Starting LLM stream for module={context.module}")
    idx = 0
    collected_tokens: List[str] = []
    try:
        async for piece in llm.stream_text(stitched):
            if not piece:
                continue
            collected_tokens.append(piece)
            yield {"type": "token", "data": _sanitize_for_json({"token": piece, "index": idx})}
            idx += 1
        print(f"[Playbook] LLM stream complete, yielded {idx} tokens")
    except Exception as e:
        print(f"[Playbook] LLM stream failed: {e}")
        # Fallback to static text if streaming fails
        fallback = generate_reasoning_text(context)
        for i, token in enumerate(fallback.split()):
            yield {"type": "token", "data": {"token": token + " ", "index": i}}
            await asyncio.sleep(0.02)
        collected_tokens = [fallback]

    # Phase 4B: Convert collected reasoning into follow-up actions
    try:
        reasoning_text = "".join(collected_tokens)
        if context.interactive_actions:
            # Suggest actions; do not execute automatically
            suggestions = extract_actions(reasoning_text, context.module)
            await write_trace(trace_path, TraceEntry(
                t=datetime.utcnow().isoformat(),
                step="action_suggestions",
                module=context.module,
                output={"suggestions": [s.get("type") for s in suggestions]}
            ))
            yield {
                "type": "intent",
                "data": _sanitize_for_json({
                    "action": "status",
                    "message": "Action suggestions available",
                    "data": {"suggestions": suggestions}
                })
            }
        else:
            # Execute automatically when interactive mode is disabled
            auto_intents = await run_auto_actions(reasoning_text, context, citations)
            if auto_intents:
                await write_trace(trace_path, TraceEntry(
                    t=datetime.utcnow().isoformat(),
                    step="auto_actions",
                    module=context.module,
                    output={"intents": len(auto_intents)}
                ))
            for intent in auto_intents:
                yield {"type": intent.get("type"), "data": _sanitize_for_json(intent.get("data"))}
                await asyncio.sleep(0.05)
    except Exception as e:
        await write_trace(trace_path, TraceEntry(
            t=datetime.utcnow().isoformat(),
            step="auto_actions_error",
            module=context.module,
            error=str(e)
        ))
    
    # Phase 5: Final result
    yield {
        "type": "final",
        "data": _sanitize_for_json({
            "module": context.module,
            "summary": f"Analysis complete for {context.module} module",
            "session_complete": True
        })
    }

def db_search_policies(query: str, limit: int = 6) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if not query:
        return results
    
    # Hybrid search with embedding (GPU-accelerated) + FTS
    from modules.embedding import get_embedding
    from db import to_vector
    
    q_emb = get_embedding(query)
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
                cur.execute(sql, (query, to_vector(q_emb), query, to_vector(q_emb), query, limit))
                for doc_id, title, text, rank_txt, rank_vec, score in cur.fetchall():
                    results.append({"id": str(doc_id), "title": title, "text": text, "relevance": float(score or 0.0), "source": title})
    except Exception as e:
        # Fallback to FTS-only if embeddings fail
        print(f"[Playbook] Hybrid search failed, falling back to FTS: {e}")
        sql2 = """
            SELECT p.doc_id, p.title, pp.text,
                   COALESCE(ts_rank_cd(pp.tsv, plainto_tsquery('english', %s)), 0) AS rank
            FROM policy_para pp
            JOIN policy p ON p.id = pp.policy_id
            WHERE pp.tsv @@ plainto_tsquery('english', %s) OR pp.embedding IS NOT NULL
            ORDER BY rank DESC
            LIMIT %s
        """
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql2, (query, query, limit))
                for doc_id, title, text, rank in cur.fetchall():
                    results.append({"id": str(doc_id), "title": title, "text": text, "relevance": float(rank), "source": title})
    return results

def db_search_precedents(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if not query:
        return results
    
    # Hybrid search with embedding (GPU-accelerated) + FTS
    from modules.embedding import get_embedding
    from db import to_vector
    
    q_emb = get_embedding(query)
    sql = """
        SELECT case_ref, decision, decision_date, summary,
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
                cur.execute(sql, (query, to_vector(q_emb), query, to_vector(q_emb), query, limit))
                for case_ref, decision, decision_date, summary, rank_txt, rank_vec, score in cur.fetchall():
                    results.append({
                        "case_ref": case_ref,
                        "decision": decision,
                        "similarity": float(score or 0.0),
                        "key_point": (summary or "")[:140],
                        "date": str(decision_date) if decision_date else None,
                    })
    except Exception as e:
        # Fallback to FTS-only
        print(f"[Playbook] Precedent hybrid search failed, falling back to FTS: {e}")
        sql2 = """
            SELECT case_ref, decision, decision_date, summary,
                   ts_rank_cd(tsv, plainto_tsquery('english', %s)) AS rank
            FROM precedent
            WHERE tsv @@ plainto_tsquery('english', %s)
            ORDER BY rank DESC
            LIMIT %s
        """
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql2, (query, query, limit))
                for case_ref, decision, decision_date, summary, rank in cur.fetchall():
                    results.append({"case_ref": case_ref, "decision": decision, "similarity": float(rank or 0.0), "key_point": (summary or "")[:140], "date": str(decision_date) if decision_date else None})
    return results

def db_search_evidence(query: str, topics: List[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Search evidence base - internal function for reasoning flow."""
    results: List[Dict[str, Any]] = []
    if not query:
        return results
    
    sql_parts = ["""
        SELECT e.id, e.title, e.type, e.topic_tags, e.geographic_scope,
               e.author, e.publisher, e.year, e.source_type, e.spatial_layer_ref,
               e.key_findings, e.status, e.reliability_flags, e.notes,
               COALESCE((SELECT COUNT(*) FROM evidence_version ev WHERE ev.evidence_id = e.id), 0) as version_count
        FROM evidence e
    """]
    where_clauses = []
    params = []
    
    # Text search across several fields (title, findings, publisher, author, geographic_scope, topic_tags)
    where_clauses.append("(" 
                        "e.title ILIKE %s OR "
                        "e.key_findings ILIKE %s OR "
                        "e.publisher ILIKE %s OR "
                        "e.author ILIKE %s OR "
                        "e.geographic_scope ILIKE %s OR "
                        "EXISTS (SELECT 1 FROM unnest(e.topic_tags) t WHERE t ILIKE %s)"
                        ")")
    like = f"%{query}%"
    params.extend([like, like, like, like, like, like])
    
    # Topic filter
    if topics:
        where_clauses.append("e.topic_tags && %s")
        params.append(topics)
    
    if where_clauses:
        sql_parts.append("WHERE " + " AND ".join(where_clauses))
    
    sql_parts.append("ORDER BY e.updated_at DESC NULLS LAST, e.id DESC LIMIT %s")
    params.append(limit)
    
    sql = " ".join(sql_parts)
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                for row in cur.fetchall():
                    results.append({
                        "id": row[0],
                        "title": row[1],
                        "type": row[2],
                        "topic_tags": row[3] or [],
                        "geographic_scope": row[4],
                        "author": row[5],
                        "publisher": row[6],
                        "year": row[7],
                        "source_type": row[8],
                        "spatial_layer_ref": row[9],
                        "key_findings": row[10],
                        "status": row[11],
                        "reliability_flags": row[12] or {},
                        "notes": row[13],
                        "version_count": row[14],
                    })
    except Exception as e:
        print(f"[Playbook] Evidence search failed: {e}")
    
    return results

def db_constraints(context: ContextPack) -> List[Dict[str, Any]]:
    lat = None
    lng = None
    if context.site_data and isinstance(context.site_data, dict):
        lat = context.site_data.get("lat")
        lng = context.site_data.get("lng")
    if lat is None or lng is None:
        return []
    results: List[Dict[str, Any]] = []
    sql = """
        WITH pt AS (
          SELECT ST_Transform(ST_SetSRID(ST_MakePoint(%s, %s), 4326), 27700) AS g
        )
        SELECT l.layer_type, COALESCE(g.name, l.name) AS name
        FROM layer l
        JOIN layer_geom g ON g.layer_id = l.id
        CROSS JOIN pt
        WHERE ST_DWithin(g.geom, pt.g, %s)
        LIMIT 25
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (lng, lat, 100))
            for layer_type, name in cur.fetchall():
                impact = "high" if (layer_type or "").lower() in {"constraint", "designation"} else "moderate"
                results.append({"type": layer_type, "name": name or "", "impact": impact})
    return results

def compute_planning_balance(policies: List[Dict[str, Any]], precedents: List[Dict[str, Any]]) -> Dict[str, Any]:
    benefits = [
        {"item": "Policy support (top hits)", "weight": "moderate" if len(policies) >= 3 else "limited"},
        {"item": "Relevant precedents", "weight": "limited" if precedents else "none"},
    ]
    harms = [
        {"item": "Unassessed design impacts", "weight": "unknown"}
    ]
    overall = "Balanced" if len(policies) >= 3 else "Uncertain"
    return {"benefits": benefits, "harms": harms, "overall": overall}

def compute_draft_decision(balance: Dict[str, Any]) -> Dict[str, Any]:
    overall = balance.get("overall", "Uncertain")
    rec = "Approval" if overall == "Balanced" else "Further information required"
    return {
        "recommendation": rec,
        "reasons": [b["item"] for b in balance.get("benefits", [])],
        "conditions": ["Materials as per schedule", "Construction management plan"],
    }

def compute_themes(text: str) -> List[Dict[str, Any]]:
    import re
    from collections import Counter
    tokens = re.findall(r"[a-zA-Z']+", (text or "").lower())
    stop = set("a an the of in on at to for and or if is are was were be been being with by from as this that these those it its their our your you we they he she them his her i me my mine ours yours theirs not no".split())
    toks = [t for t in tokens if t not in stop and len(t) > 2]
    bigrams = [f"{toks[i]} {toks[i+1]}" for i in range(len(toks)-1)] if len(toks) > 1 else []
    top = Counter(bigrams).most_common(5)
    out: List[Dict[str, Any]] = []
    for phrase, count in top:
        sentiment = "negative" if any(w in phrase for w in ["concern", "object", "oppose", "traffic", "noise"]) else "positive"
        out.append({"theme": phrase.title(), "count": count, "sentiment": sentiment})
    return out

def generate_reasoning_text(context: ContextPack) -> str:
    """Generate reasoning narrative based on module."""
    
    templates = {
        "dm": "Based on the proposal details and local planning policy, I have identified the key material considerations. The scheme delivers housing in a sustainable location and demonstrates acceptable design quality. While there are some concerns regarding height and massing, these can be addressed through conditions. On balance, I recommend approval.",
        
        "policy": "Analyzing policy consistency across the plan. The draft housing policy aligns with national guidance but may benefit from clearer integration with environmental policies. Consider cross-referencing green infrastructure requirements.",
        
        "strategy": "Comparing strategic options for housing delivery. Option B (brownfield intensification) scores higher on sustainability metrics and infrastructure efficiency, though delivers fewer units. Option A offers greater capacity but requires significant new infrastructure investment.",
        
        "vision": "Visual analysis of the design proposal shows general compliance with local design codes. The building line is maintained and materials are appropriate. Height slightly exceeds the prevailing context but this may be acceptable given the site's location near the transport hub.",
        
        "feedback": "Analysis of consultation responses reveals two dominant themes: traffic and parking concerns (47 responses) and support for new housing (32 responses). Objections are concentrated in the immediate area, while support is more geographically distributed.",
        
        "evidence": "The evidence base reveals multiple site constraints including conservation area designation and flood risk (Zone 2). However, the site is also within a town centre location with excellent public transport access. 12 relevant policies apply, primarily focused on design quality and heritage protection."
    }
    
    return templates.get(context.module, "Analysis in progress...")


def _domain_allowed(domain: str, module: str) -> bool:
    domain = (domain or "").lower()
    allowed = ALLOWED_BY_MODULE.get(module, [])
    for d in allowed:
        if domain == d or domain.endswith("." + d):
            return True
    return False
