"""Reasoning Executor
Turns reasoning into concrete actions via LLM with structured output.
Traces context from knowledge graph, spatial layers, evidence base, etc.
"""
from typing import List, Dict, Any
import json

from .context import ContextPack
from .llm import call_llm
from . import playbook as pb


async def extract_actions(reasoning: str, context: ContextPack) -> List[Dict[str, Any]]:
    """
    Use LLM with structured output to determine what actions to take.
    The LLM considers:
    - User prompt and reasoning so far
    - Module context (evidence/policy/strategy/vision/feedback/dm)
    - Available tools (search evidence, search policies, get constraints, etc.)
    """
    
    # Build context for action planning
    tools_available = {
        "evidence": ["search_evidence", "evidence_gaps", "evidence_dependencies"],
        "policy": ["search_policies", "policy_graph", "check_consistency"],
        "strategy": ["scenario_compare", "planning_balance", "viability_check"],
        "vision": ["visual_compliance", "design_standards"],
        "feedback": ["cluster_themes", "sentiment_analysis"],
        "dm": ["search_policies", "precedents", "spatial_constraints", "planning_balance", "draft_decision"]
    }
    
    available_tools = tools_available.get(context.module, [])
    
    # Gather relevant context traces
    context_traces = []
    
    # Knowledge graph context (policy relationships, evidence links)
    if context.module in ["policy", "evidence", "strategy"]:
        # TODO: query knowledge graph for related entities
        context_traces.append({"type": "knowledge_graph", "status": "not_yet_implemented"})
    
    # Spatial context (constraints, designations, site characteristics)
    if context.site_data and context.module in ["dm", "strategy", "vision"]:
        try:
            constraints = pb.db_constraints(context) or []
            context_traces.append({
                "type": "spatial_context",
                "constraints": [c.get("type") for c in constraints],
                "count": len(constraints)
            })
        except:
            pass
    
    # Evidence context (what evidence exists for this topic)
    if context.module in ["evidence", "policy", "strategy"]:
        # TODO: quick evidence availability check
        context_traces.append({"type": "evidence_context", "status": "not_yet_implemented"})
    
    # Prompt for structured action planning
    action_prompt = f"""You are a planning assistant reasoning engine. Based on the user's request and your reasoning so far, determine what actions to take.

**User prompt:** {context.prompt}

**Module:** {context.module}

**Reasoning so far:** {reasoning[:500]}

**Available tools:** {', '.join(available_tools)}

**Context traces:** {json.dumps(context_traces, indent=2)}

Respond with a JSON object:
{{
  "actions": [
    {{"type": "tool_name", "query": "specific query or null", "rationale": "why this action"}},
    ...
  ],
  "reasoning": "brief explanation of action plan"
}}

Keep to 1-3 actions. Be specific about queries."""

    try:
        response = await call_llm(
            messages=[{"role": "user", "content": action_prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        # Parse structured response
        result = json.loads(response)
        actions = result.get("actions", [])
        
        # Validate and normalize actions
        normalized = []
        for a in actions:
            if isinstance(a, dict) and "type" in a:
                normalized.append({
                    "type": a["type"],
                    "query": a.get("query"),
                    "rationale": a.get("rationale", "")
                })
        
        return normalized
        
    except Exception as e:
        # Fallback to simple heuristic if LLM fails
        return _fallback_extract_actions(reasoning, context.module)


def _fallback_extract_actions(reasoning: str, module: str) -> List[Dict[str, Any]]:
    """Simple keyword fallback when LLM action extraction fails."""
    text = (reasoning or "").lower()
    actions: List[Dict[str, Any]] = []

    def want(words: List[str]) -> bool:
        return any(w in text for w in words)

    # Evidence module
    if module == "evidence":
        if want(["search", "find", "show", "evidence", "housing", "transport"]):
            actions.append({"type": "search_evidence", "query": None})
        if want(["gap", "missing", "stale"]):
            actions.append({"type": "evidence_gaps", "query": None})
    
    # Common DM actions
    if want(["policy", "applicable"]):
        actions.append({"type": "search_policies", "query": None})
    if want(["precedent", "appeal"]):
        actions.append({"type": "precedents", "query": None})
    if want(["constraint", "designation"]):
        actions.append({"type": "spatial_constraints", "query": None})
    if want(["planning balance"]):
        actions.append({"type": "planning_balance", "query": None})
    if want(["draft decision", "recommend"]):
        actions.append({"type": "draft_decision", "query": None})
    
    return actions


async def execute_actions(actions: List[Dict[str, Any]], context: ContextPack, citations: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    """Execute planned actions using available services and format intents."""
    intents: List[Dict[str, Any]] = []
    citations = citations or []

    # Helper to push an intent
    def show(panel: str, data: Dict[str, Any]) -> None:
        intents.append({
            "type": "intent",
            "data": {
                "action": "show_panel",
                "panel": panel,
                "data": data,
            }
        })

    for a in actions:
        t = a.get("type")
        try:
            # Evidence module actions
            if t == "search_evidence":
                # Extract topics from query
                topics = []
                query_lower = (a.get("query") or context.prompt).lower()
                if "housing" in query_lower:
                    topics.append("housing")
                if "transport" in query_lower:
                    topics.append("transport")
                if any(w in query_lower for w in ["environment", "climate"]):
                    topics.append("climate")
                
                items = pb.db_search_evidence(
                    a.get("query") or context.prompt,
                    topics=topics if topics else None,
                    limit=50
                )
                show("evidence_browser", {"items": items, "filters": {}, "citations": citations})
            
            elif t == "evidence_gaps":
                # TODO: implement gap analysis
                show("evidence_gaps", {"gaps": [], "stale": [], "weak_links": [], "citations": citations})
            
            elif t == "evidence_dependencies":
                # TODO: implement dependency graph
                show("dependency_graph", {"nodes": [], "edges": [], "citations": citations})
            
            # Policy/DM actions
            elif t in ["search_policies", "policy.search"]:
                hits = pb.db_search_policies(a.get("query") or context.prompt, limit=8)
                show("applicable_policies", {"policies": hits, "citations": citations})

            elif t in ["precedents", "precedent.search"]:
                hits = pb.db_search_precedents(a.get("query") or context.prompt, limit=6)
                show("precedents", {"items": hits, "citations": citations})

            elif t in ["spatial_constraints", "spatial.constraints"]:
                cons = pb.db_constraints(context) or []
                show("evidence_snapshot", {"constraints": cons, "policy_count": len(cons), "citations": citations})

            elif t in ["planning_balance", "planning.balance"]:
                pol = pb.db_search_policies(context.prompt, limit=6)
                pre = pb.db_search_precedents(context.prompt, limit=5)
                bal = pb.compute_planning_balance(pol, pre)
                show("planning_balance", {"balance": bal, "policies": pol, "precedents": pre, "citations": citations})

            elif t in ["draft_decision", "draft.decision"]:
                pol = pb.db_search_policies(context.prompt, limit=6)
                pre = pb.db_search_precedents(context.prompt, limit=5)
                bal = pb.compute_planning_balance(pol, pre)
                dec = pb.compute_draft_decision(bal)
                show("draft_decision", {"decision": dec, "balance": bal, "citations": citations})

        except Exception as e:  # keep the loop resilient
            intents.append({
                "type": "intent",
                "data": {
                    "action": "notify",
                    "level": "warning",
                    "message": f"Auto-action '{t}' failed: {e}",
                }
            })

    return intents


async def run_auto_actions(reasoning_text: str, context: ContextPack, citations: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    actions = await extract_actions(reasoning_text, context)
    return await execute_actions(actions, context, citations)
