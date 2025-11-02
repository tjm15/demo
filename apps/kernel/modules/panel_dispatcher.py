"""Panel dispatcher - executes data retrieval and emission for planned panels.

Takes a panel plan (list of panel names) and generates the data payload
for each panel by calling the appropriate DB/service functions.
"""
from __future__ import annotations
from typing import Dict, Any, List
import asyncio
from modules.context import ContextPack
from db import get_conn

# Import search functions (will be defined in same file as playbook currently uses)
# We'll refactor these to be importable


async def dispatch_panel(
    panel_name: str,
    context: ContextPack,
    citations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute data retrieval for a specific panel.
    
    Returns:
        Dict with panel type and data payload ready for emission.
    """
    
    if panel_name == "applicable_policies":
        from modules.playbook import db_search_policies
        policies = db_search_policies(context.prompt, limit=6)
        return {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "applicable_policies",
                "data": {"policies": policies, "citations": citations},
            }
        }
    
    elif panel_name == "precedents":
        from modules.playbook import db_search_precedents
        precedents = db_search_precedents(context.prompt, limit=5)
        return {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "precedents",
                "data": {"precedents": precedents},
            }
        }
    
    elif panel_name == "map":
        from modules.playbook import db_constraints
        lat = (context.site_data or {}).get("lat") if isinstance(context.site_data, dict) else None
        lng = (context.site_data or {}).get("lng") if isinstance(context.site_data, dict) else None
        
        if lat is None or lng is None:
            # Should have been filtered by planner, but skip if missing
            return None
        
        constraints = db_constraints(context)
        return {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "map",
                "data": {
                    "center": {"lat": lat, "lng": lng},
                    "constraints": constraints,
                },
            }
        }
    
    elif panel_name == "evidence_snapshot":
        from modules.playbook import db_constraints
        constraints = db_constraints(context) or []
        return {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "evidence_snapshot",
                "data": {
                    "constraints": constraints,
                    "policy_count": len(constraints),
                    "citations": citations or [],
                }
            }
        }
    
    elif panel_name == "evidence_browser":
        from modules.playbook import db_search_evidence
        items = db_search_evidence(context.prompt or "", limit=50)
        return {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "evidence_browser",
                "data": {
                    "items": items,
                    "filters": {
                        "topics": [],
                        "scope": "db"
                    }
                }
            }
        }
    
    elif panel_name == "planning_balance":
        from modules.playbook import db_search_policies, db_search_precedents, compute_planning_balance
        policies = db_search_policies(context.prompt, limit=6)
        precedents = db_search_precedents(context.prompt, limit=5)
        balance = compute_planning_balance(policies, precedents)
        return {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "planning_balance",
                "data": balance,
            }
        }
    
    elif panel_name == "draft_decision":
        from modules.playbook import db_search_policies, db_search_precedents, compute_planning_balance, compute_draft_decision
        policies = db_search_policies(context.prompt, limit=6)
        precedents = db_search_precedents(context.prompt, limit=5)
        balance = compute_planning_balance(policies, precedents)
        draft = compute_draft_decision(balance)
        return {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "draft_decision",
                "data": draft,
            }
        }
    
    elif panel_name == "policy_editor":
        from modules.playbook import db_search_policies
        policies = db_search_policies(context.prompt or "policy", limit=1)
        draft_text = (policies[0]["text"] if policies else "")
        return {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "policy_editor",
                "data": {"draft_text": draft_text, "suggestions": []},
            }
        }
    
    elif panel_name == "scenario_compare":
        from modules.playbook import db_search_policies
        # Create two simple scenarios based on query
        p1 = db_search_policies(context.prompt + " option A", limit=4)
        p2 = db_search_policies(context.prompt + " option B", limit=4)
        return {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "scenario_compare",
                "data": {
                    "scenarios": [
                        {"name": "Option A", "score": len(p1)},
                        {"name": "Option B", "score": len(p2)}
                    ]
                }
            }
        }
    
    elif panel_name == "visual_compliance":
        return {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "visual_compliance",
                "data": {"compliance": []}
            }
        }
    
    elif panel_name == "consultation_themes":
        from modules.playbook import compute_themes
        themes = compute_themes(context.prompt)
        return {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "consultation_themes",
                "data": {"themes": themes}
            }
        }
    
    elif panel_name == "key_issues_matrix":
        return {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "key_issues_matrix",
                "data": {"issues": []}
            }
        }
    
    elif panel_name == "conflict_heatmap":
        return {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "conflict_heatmap",
                "data": {"conflicts": []}
            }
        }
    
    elif panel_name == "doc_viewer":
        return {
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": "doc_viewer",
                "data": {
                    "doc_id": "unknown",
                    "title": "Document",
                    "paragraphs": []
                }
            }
        }
    
    else:
        print(f"[Dispatcher] Unknown panel type: {panel_name}")
        return None
