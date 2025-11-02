"""Playbook execution - orchestrates reasoning flow using live services (DB)."""
import asyncio
from typing import AsyncGenerator, Dict, Any, List
from pathlib import Path
from datetime import datetime

from modules.context import ContextPack
from modules.trace import TraceEntry, write_trace
from modules import llm
from modules import proxy_client
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

async def execute_playbook(context: ContextPack, trace_path: Path) -> AsyncGenerator[Dict[str, Any], None]:
    """Execute reasoning playbook for given module."""
    
    # Phase 1: Planning
    yield {
        "type": "intent",
        "data": {
            "action": "init_workspace",
            "module": context.module,
            "message": f"Initializing {context.module.upper()} module workspace..."
        }
    }
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
        "data": {
            "action": "show_panel",
            "panel": "evidence_snapshot" if context.module == "evidence" else "applicable_policies",
            "message": "Retrieving relevant policies..."
        }
    }
    await asyncio.sleep(0.1)
    
    # Phase 3: Analysis
    if context.module == "dm":
        # Development Management flow using DB-backed panels
        # 0) Map if site coordinates provided
        lat = (context.site_data or {}).get("lat") if isinstance(context.site_data, dict) else None
        lng = (context.site_data or {}).get("lng") if isinstance(context.site_data, dict) else None
        if lat is not None and lng is not None:
            dm_constraints = db_constraints(context)
            yield {
                "type": "intent",
                "data": {
                    "action": "show_panel",
                    "panel": "map",
                    "data": {"center": {"lat": lat, "lng": lng}, "constraints": dm_constraints},
                },
            }
            await asyncio.sleep(0.1)
        # 1) Applicable policies (text search on prompt)
        policies = db_search_policies(context.prompt, limit=6)
        print(f"DEBUG: Retrieved {len(policies)} policies for prompt: {context.prompt}")
        yield {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "applicable_policies",
                "data": {"policies": policies, "citations": citations},
            },
        }
        await asyncio.sleep(0.1)

        # 2) Precedents (search summaries)
        precedents = db_search_precedents(context.prompt, limit=5)
        yield {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "precedents",
                "data": {"precedents": precedents},
            },
        }
        await asyncio.sleep(0.1)

        # 3) Planning balance (heuristic from counts)
        balance = compute_planning_balance(policies, precedents)
        yield {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "planning_balance",
                "data": balance,
            },
        }
        await asyncio.sleep(0.1)

        # 4) Draft decision (simple rule-based summary)
        draft = compute_draft_decision(balance)
        yield {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "draft_decision",
                "data": draft,
            },
        }
    
    elif context.module == "policy":
        # Policy flow: show editor seeded from top policy result
        policies = db_search_policies(context.prompt or "policy", limit=1)
        draft_text = (policies[0]["text"] if policies else "")
        yield {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "policy_editor",
                "data": {"draft_text": draft_text, "suggestions": []},
            },
        }
    
    elif context.module == "strategy":
        # Strategy flow minimal: reuse planning balance based on policy hits for two queries
        p1 = db_search_policies(context.prompt + " option A", limit=4)
        p2 = db_search_policies(context.prompt + " option B", limit=4)
        yield {"type": "intent", "data": {"action": "show_panel", "panel": "scenario_compare", "data": {"scenarios": [{"name": "Option A", "score": len(p1)}, {"name": "Option B", "score": len(p2)}]}}}
        await asyncio.sleep(0.1)
        yield {"type": "intent", "data": {"action": "show_panel", "panel": "planning_balance", "data": compute_planning_balance(p1, [])}}
    
    elif context.module == "vision":
        # Vision flow: placeholder compliance check panel (no image processing yet)
        yield {"type": "intent", "data": {"action": "show_panel", "panel": "visual_compliance", "data": {"compliance": []}}}
    
    elif context.module == "feedback":
        # Feedback flow: call service via simple in-process function (reuse minimal theme logic here)
        themes = compute_themes(context.prompt)
        yield {"type": "intent", "data": {"action": "show_panel", "panel": "consultation_themes", "data": {"themes": themes}}}
    
    elif context.module == "evidence":
        # Evidence flow: map + spatial constraints + policies
        lat = (context.site_data or {}).get("lat") if isinstance(context.site_data, dict) else None
        lng = (context.site_data or {}).get("lng") if isinstance(context.site_data, dict) else None
        
        constraints = db_constraints(context)
        
        # Show map panel with constraints if we have coordinates
        if lat is not None and lng is not None:
            yield {
                "type": "intent",
                "data": {
                    "action": "show_panel",
                    "panel": "map",
                    "data": {
                        "center": {"lat": lat, "lng": lng},
                        "constraints": constraints,
                    },
                },
            }
            await asyncio.sleep(0.1)
        
        yield {"type": "intent", "data": {"action": "show_panel", "panel": "evidence_snapshot", "data": {"constraints": constraints, "policy_count": len(constraints), "citations": citations}}}
        await asyncio.sleep(0.1)
        policies = db_search_policies(context.prompt, limit=6)
        yield {"type": "intent", "data": {"action": "show_panel", "panel": "applicable_policies", "data": {"policies": policies, "citations": citations}}}
    
    # Phase 4: Streaming reasoning tokens (via LLM if available)
    sys_prompt = llm.build_system_prompt(context.module)
    usr_prompt = llm.build_user_prompt(context.module, context.prompt, context.site_data, context.proposal_data)
    stitched = f"SYSTEM:\n{sys_prompt}\n\nUSER:\n{usr_prompt}"

    print(f"[Playbook] Starting LLM stream for module={context.module}")
    idx = 0
    try:
        async for piece in llm.stream_text(stitched):
            if not piece:
                continue
            yield {"type": "token", "data": {"token": piece, "index": idx}}
            idx += 1
        print(f"[Playbook] LLM stream complete, yielded {idx} tokens")
    except Exception as e:
        print(f"[Playbook] LLM stream failed: {e}")
        # Fallback to static text if streaming fails
        fallback = generate_reasoning_text(context)
        for i, token in enumerate(fallback.split()):
            yield {"type": "token", "data": {"token": token + " ", "index": i}}
            await asyncio.sleep(0.02)
    
    # Phase 5: Final result
    yield {
        "type": "final",
        "data": {
            "module": context.module,
            "summary": f"Analysis complete for {context.module} module",
            "session_complete": True
        }
    }

def db_search_policies(query: str, limit: int = 6) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if not query:
        return results
    
    # Use generated tsv column for better performance
    # OR condition ensures we get results even if not all terms match
    sql = """
        SELECT p.doc_id, p.title, pp.text,
               COALESCE(ts_rank_cd(pp.tsv, plainto_tsquery('english', %s)), 0) AS rank
        FROM policy_para pp
        JOIN policy p ON p.id = pp.policy_id
        WHERE pp.tsv @@ plainto_tsquery('english', %s) OR pp.embedding IS NOT NULL
        ORDER BY rank DESC
        LIMIT %s
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (query, query, limit))
                for doc_id, title, text, rank in cur.fetchall():
                    results.append({"id": str(doc_id), "title": title, "text": text, "relevance": float(rank), "source": title})
    except Exception as e:
        # Fallback to ILIKE
        like = f"%{query}%"
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT p.doc_id, p.title, pp.text FROM policy_para pp JOIN policy p ON p.id = pp.policy_id WHERE pp.text ILIKE %s LIMIT %s",
                    (like, limit),
                )
                for doc_id, title, text in cur.fetchall():
                    results.append({"id": str(doc_id), "title": title, "text": text, "relevance": 0.5, "source": title})
    return results

def db_search_precedents(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if not query:
        return results
    
    # Use generated tsv column
    sql = """
        SELECT case_ref, decision, decision_date, summary,
               ts_rank_cd(tsv, plainto_tsquery('english', %s)) AS rank
        FROM precedent
        WHERE tsv @@ plainto_tsquery('english', %s)
        ORDER BY rank DESC
        LIMIT %s
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (query, query, limit))
                for case_ref, decision, decision_date, summary, rank in cur.fetchall():
                    results.append({
                        "case_ref": case_ref,
                        "decision": decision,
                        "similarity": float(rank or 0.0),
                        "key_point": (summary or "")[:140],
                        "date": str(decision_date) if decision_date else None,
                    })
    except Exception:
        # Fallback to ILIKE
        like = f"%{query}%"
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT case_ref, decision, decision_date, summary FROM precedent WHERE summary ILIKE %s LIMIT %s", (like, limit))
                for case_ref, decision, decision_date, summary in cur.fetchall():
                    results.append({"case_ref": case_ref, "decision": decision, "similarity": 0.5, "key_point": (summary or "")[:140], "date": str(decision_date) if decision_date else None})
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
