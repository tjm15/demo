"""
Evidence Base Module - handles evidence discovery, validation, and analysis
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from modules.context import ContextPack
from modules.trace import TraceEntry, write_trace
from pathlib import Path
import json

async def evidence_playbook(context: ContextPack, trace_path: Path) -> List[Dict[str, Any]]:
    """
    Execute evidence base reasoning workflow.
    
    Phases:
    1. Parse intent (search, validate, link, gap analysis)
    2. Retrieve evidence items
    3. Analyze quality and currency
    4. Generate intents for UI panels
    """
    intents = []
    
    await write_trace(trace_path, TraceEntry(
        t=datetime.utcnow().isoformat(),
        step="evidence_start",
        input={"prompt": context.prompt}
    ))
    
    # Determine user intent
    prompt_lower = context.prompt.lower()
    
    # Phase 1: Determine action type
    if any(kw in prompt_lower for kw in ["search", "find", "show", "list"]):
        action = "search"
    elif any(kw in prompt_lower for kw in ["gap", "missing", "weak", "stale"]):
        action = "gap_analysis"
    elif any(kw in prompt_lower for kw in ["link", "connect", "dependency", "depends"]):
        action = "dependencies"
    elif any(kw in prompt_lower for kw in ["validate", "check", "quality", "currency"]):
        action = "validate"
    else:
        action = "search"  # default
    
    await write_trace(trace_path, TraceEntry(
        t=datetime.utcnow().isoformat(),
        step="determine_action",
        output={"action": action}
    ))
    
    # Phase 2: Execute action
    if action == "search":
        # Extract search parameters
        topics = []
        if "housing" in prompt_lower:
            topics.append("housing")
        if "transport" in prompt_lower:
            topics.append("transport")
        if "economy" in prompt_lower or "employment" in prompt_lower:
            topics.append("economy")
        if "environment" in prompt_lower or "climate" in prompt_lower:
            topics.append("climate")
        
        # Call backend service to get actual evidence items
        from services.evidence import search_evidence, EvidenceSearchRequest
        try:
            results = await search_evidence(EvidenceSearchRequest(
                q=context.prompt,
                topic=topics if topics else None,
                scope="db"
            ))
            items = [item.dict() for item in results]
        except Exception as e:
            await write_trace(trace_path, TraceEntry(
                t=datetime.utcnow().isoformat(),
                step="evidence_search_error",
                output={"error": str(e)}
            ))
            items = []
        
        # Emit search intent with actual data
        intents.append({
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "evidence_browser",
                "id": f"evidence_browser_{int(datetime.utcnow().timestamp())}",
                "data": {
                    "items": items,
                    "filters": {
                        "topics": topics,
                        "scope": "db"
                    }
                }
            }
        })
        
        await write_trace(trace_path, TraceEntry(
            t=datetime.utcnow().isoformat(),
            step="evidence_search",
            output={"topics": topics}
        ))
    
    elif action == "gap_analysis":
        # Emit gap analysis panel
        intents.append({
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "evidence_gaps",
                "id": f"evidence_gaps_{int(datetime.utcnow().timestamp())}",
                "data": {
                    "no_evidence": [],
                    "stale_evidence": [],
                    "weak_links_only": []
                }
            }
        })
        
        await write_trace(trace_path, TraceEntry(
            t=datetime.utcnow().isoformat(),
            step="gap_analysis",
            output={}
        ))
    
    elif action == "dependencies":
        # Emit dependency graph
        intents.append({
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "dependency_graph",
                "id": f"dependency_graph_{int(datetime.utcnow().timestamp())}",
                "data": {
                    "nodes": [],
                    "edges": []
                }
            }
        })
        
        await write_trace(trace_path, TraceEntry(
            t=datetime.utcnow().isoformat(),
            step="dependency_graph",
            output={}
        ))
    
    elif action == "validate":
        # Emit both search and gaps
        intents.append({
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "evidence_browser",
                "id": f"evidence_browser_{int(datetime.utcnow().timestamp())}",
                "data": {"items": [], "filters": {}}
            }
        })
        intents.append({
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "evidence_gaps",
                "id": f"evidence_gaps_{int(datetime.utcnow().timestamp())}",
                "data": {
                    "no_evidence": [],
                    "stale_evidence": [],
                    "weak_links_only": []
                }
            }
        })
    
    # Final summary message
    intents.append({
        "type": "token",
        "data": {"content": f"\n\nEvidence base analysis complete. Action: {action}"}
    })
    
    intents.append({
        "type": "final",
        "data": {"summary": f"Evidence {action} executed", "action": action}
    })
    
    await write_trace(trace_path, TraceEntry(
        t=datetime.utcnow().isoformat(),
        step="evidence_complete",
        output={"intents_count": len(intents)}
    ))
    
    return intents
