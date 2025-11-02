"""LLM-driven panel planner for adaptive UI generation.

The planner analyzes the user's query and context, then decides which panels
to show and in what order. This replaces hardcoded module->panel mappings
with conversational reasoning.
"""
from __future__ import annotations
import json
from typing import List, Dict, Any, Optional
from modules.context import ContextPack
from modules import llm

# Registry of available panels per module (synced with frontend)
PANEL_REGISTRY = {
    "dm": {
        "applicable_policies": "List of relevant planning policies for the proposal",
        "key_issues_matrix": "Matrix of planning issues and their policy alignment",
        "precedents": "Relevant appeal decisions and case law",
        "planning_balance": "Weighing of benefits and harms for decision",
        "draft_decision": "Recommended decision with reasons and conditions",
        "evidence_snapshot": "Overview of site constraints and available documents",
        "map": "Interactive map with spatial layers (requires lat/lng)",
        "doc_viewer": "View policy documents with paragraph highlighting",
    },
    "evidence": {
        "evidence_browser": "Search and browse evidence base with filters",
        "evidence_snapshot": "Overview of site constraints and available documents",
        "evidence_gaps": "Analysis of evidence gaps and stale evidence",
        "dependency_graph": "Evidence-policy dependency graph",
        "map": "Interactive map with spatial layers (requires lat/lng)",
        "applicable_policies": "List of relevant planning policies",
        "doc_viewer": "View policy documents with paragraph highlighting",
    },
    "policy": {
        "policy_editor": "Edit and validate policy wording",
        "conflict_heatmap": "Visualization of policy conflicts and tensions",
        "applicable_policies": "List of relevant planning policies",
        "precedents": "Relevant appeal decisions and case law",
        "doc_viewer": "View policy documents with paragraph highlighting",
    },
    "strategy": {
        "scenario_compare": "Side-by-side comparison of strategy options",
        "planning_balance": "Weighing of benefits and harms for decision",
        "applicable_policies": "List of relevant planning policies",
    },
    "vision": {
        "visual_compliance": "Design code compliance check with visual analysis",
        "applicable_policies": "List of relevant planning policies",
    },
    "feedback": {
        "consultation_themes": "Thematic analysis of consultation feedback",
        "applicable_policies": "List of relevant planning policies",
    },
}

# Fallback panel sequences if LLM fails
FALLBACK_PANELS = {
    "dm": ["applicable_policies", "precedents", "planning_balance", "draft_decision"],
    "evidence": ["evidence_browser", "evidence_snapshot"],
    "policy": ["policy_editor"],
    "strategy": ["scenario_compare", "planning_balance"],
    "vision": ["visual_compliance"],
    "feedback": ["consultation_themes"],
}


def build_planning_prompt(context: ContextPack) -> str:
    """Build prompt for LLM panel planner."""
    module = context.module
    available = PANEL_REGISTRY.get(module, {})
    
    # Format available panels
    panel_list = "\n".join([
        f"- {name}: {desc}"
        for name, desc in available.items()
    ])
    
    # Context summary
    has_coords = False
    if context.site_data and isinstance(context.site_data, dict):
        has_coords = "lat" in context.site_data and "lng" in context.site_data
    
    prompt = f"""You are planning the UI response for a planning assistant query.

Module: {module.upper()}
User query: {context.prompt}
Has site coordinates: {has_coords}
Run mode: {context.run_mode}

Available panels for this module:
{panel_list}

Your task:
1. Analyze what the user is asking for
2. Select which panels would be most helpful (1-4 panels recommended)
3. Order them logically (e.g., show evidence before conclusions)

Constraints:
- The 'map' panel requires site coordinates (lat/lng)
- Prioritize panels that directly answer the user's question
- In 'stable' mode, prefer 2-3 core panels; in 'deep' mode you can show more
- Always include at least one substantive panel

Respond with ONLY a JSON array of panel names, like:
["applicable_policies", "precedents", "draft_decision"]

Do not include explanations or markdown formatting.
"""
    return prompt


async def plan_panels(context: ContextPack) -> List[str]:
    """Use LLM to decide which panels to show for this query.
    
    Returns:
        List of panel names in display order.
        Falls back to module defaults if LLM fails or returns invalid JSON.
    """
    # Build planning prompt
    prompt = build_planning_prompt(context)
    
    try:
        # Get LLM response (non-streaming)
        response = await llm.generate_text(prompt, model=None)
        
        # Parse JSON
        # Strip markdown code fences if present
        response = response.strip()
        if response.startswith("```"):
            # Extract content between fences
            lines = response.split("\n")
            response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
        
        panel_plan = json.loads(response)
        
        if not isinstance(panel_plan, list):
            raise ValueError("LLM returned non-list")
        
        # Validate panel names against registry
        available = set(PANEL_REGISTRY.get(context.module, {}).keys())
        validated = [p for p in panel_plan if p in available]
        
        if not validated:
            raise ValueError("No valid panels in LLM response")
        
        # Apply coordinate constraint for map
        has_coords = False
        if context.site_data and isinstance(context.site_data, dict):
            has_coords = "lat" in context.site_data and "lng" in context.site_data
        
        if "map" in validated and not has_coords:
            validated.remove("map")
        
        # Limit to reasonable count (max 5 panels)
        validated = validated[:5]
        
        print(f"[PanelPlanner] LLM selected panels: {validated}")
        return validated
        
    except Exception as e:
        print(f"[PanelPlanner] Planning failed: {e}, using fallback")
        fallback = FALLBACK_PANELS.get(context.module, ["applicable_policies"])
        
        # Apply coordinate constraint to fallback too
        has_coords = False
        if context.site_data and isinstance(context.site_data, dict):
            has_coords = "lat" in context.site_data and "lng" in context.site_data
        
        if "map" in fallback and not has_coords:
            fallback = [p for p in fallback if p != "map"]
        
        return fallback


def get_panel_description(module: str, panel_name: str) -> str:
    """Get human-readable description of a panel."""
    return PANEL_REGISTRY.get(module, {}).get(panel_name, panel_name)
