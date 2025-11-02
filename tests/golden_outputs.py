"""
Golden Outputs - Expected panel configurations for test scenarios
These serve as snapshot references for regression testing
"""

from typing import List, Dict, Any

# =============================================================================
# Development Management (DM) Module
# =============================================================================

DM_SCENARIO_1 = {
    "name": "Residential Intensification near Conservation Area",
    "prompt": "45 unit residential development, 6 storeys, near conservation area",
    "module": "dm",
    "expected_panels": [
        {
            "type": "evidence_snapshot",
            "required_fields": ["site", "constraints"],
            "constraints_min": 1,
        },
        {
            "type": "applicable_policies",
            "required_fields": ["policies"],
            "policies_min": 3,
        },
        {
            "type": "key_issues_matrix",
            "required_fields": ["issues"],
            "issues_min": 2,
        },
        {
            "type": "precedents",
            "required_fields": ["cases"],
            "cases_min": 1,
        },
        {
            "type": "planning_balance",
            "required_fields": ["benefits", "harms"],
        },
        {
            "type": "draft_decision",
            "required_fields": ["recommendation", "reasons"],
        },
    ],
    "reasoning_must_contain": ["conservation", "height", "density", "heritage"],
}

DM_SCENARIO_2 = {
    "name": "Change of Use - Office to Residential",
    "prompt": "Change of use from office to 12 residential flats",
    "module": "dm",
    "expected_panels": [
        {
            "type": "applicable_policies",
            "required_fields": ["policies"],
        },
        {
            "type": "key_issues_matrix",
            "required_fields": ["issues"],
        },
        {
            "type": "planning_balance",
            "required_fields": ["benefits", "harms"],
        },
        {
            "type": "draft_decision",
            "required_fields": ["recommendation", "reasons"],
        },
    ],
    "reasoning_must_contain": ["change of use", "residential", "office"],
}

# =============================================================================
# Evidence Base Module
# =============================================================================

EVIDENCE_SCENARIO_1 = {
    "name": "Site Constraints Analysis with Coordinates",
    "prompt": "Site at 51.5074, -0.1278 for residential development",
    "module": "evidence",
    "expected_panels": [
        {
            "type": "evidence_snapshot",
            "required_fields": ["site", "constraints"],
            "site_must_have": ["lat", "lng"],
        },
        {
            "type": "map",
            "required_fields": ["center"],
        },
    ],
    "reasoning_must_contain": ["constraint", "site"],
}

# =============================================================================
# Policy Module
# =============================================================================

POLICY_SCENARIO_1 = {
    "name": "Housing Policy Review",
    "prompt": "Review housing policy H1 for consistency with London Plan",
    "module": "policy",
    "expected_panels": [
        {
            "type": "policy_editor",
            "required_fields": ["policy_id", "original_text"],
        },
        {
            "type": "applicable_policies",
            "required_fields": ["policies"],
        },
    ],
    "reasoning_must_contain": ["consistency", "London Plan", "policy"],
}

POLICY_SCENARIO_2 = {
    "name": "Draft New Policy",
    "prompt": "Draft policy for sustainable transport in new developments",
    "module": "policy",
    "expected_panels": [
        {
            "type": "policy_editor",
            "required_fields": ["policy_id", "suggested_text"],
        },
        {
            "type": "applicable_policies",
            "required_fields": ["policies"],
        },
    ],
    "reasoning_must_contain": ["sustainable", "transport", "policy"],
}

# =============================================================================
# Strategy Module
# =============================================================================

STRATEGY_SCENARIO_1 = {
    "name": "Housing Strategy Comparison",
    "prompt": "Compare urban extension vs brownfield intensification for 5000 homes",
    "module": "strategy",
    "expected_panels": [
        {
            "type": "scenario_compare",
            "required_fields": ["scenarios"],
            "scenarios_min": 2,
        },
        {
            "type": "planning_balance",
            "required_fields": ["benefits", "harms"],
        },
    ],
    "reasoning_must_contain": ["urban extension", "brownfield", "comparison"],
}

# =============================================================================
# Vision Module
# =============================================================================

VISION_SCENARIO_1 = {
    "name": "Design Compliance Check",
    "prompt": "Check design compliance for 8-storey mixed-use scheme",
    "module": "vision",
    "expected_panels": [
        {
            "type": "visual_compliance",
            "required_fields": ["checks"],
        },
    ],
    "reasoning_must_contain": ["design", "compliance"],
}

# =============================================================================
# Feedback Module
# =============================================================================

FEEDBACK_SCENARIO_1 = {
    "name": "Consultation Response Analysis",
    "prompt": "Analyze consultation responses on proposed local plan",
    "module": "feedback",
    "expected_panels": [
        {
            "type": "consultation_themes",
            "required_fields": ["themes"],
            "themes_min": 1,
        },
    ],
    "reasoning_must_contain": ["consultation", "feedback", "themes"],
}

# =============================================================================
# Golden Output Registry
# =============================================================================

GOLDEN_OUTPUTS = {
    "dm_residential_conservation": DM_SCENARIO_1,
    "dm_change_of_use": DM_SCENARIO_2,
    "evidence_site_coords": EVIDENCE_SCENARIO_1,
    "policy_review": POLICY_SCENARIO_1,
    "policy_draft": POLICY_SCENARIO_2,
    "strategy_housing_compare": STRATEGY_SCENARIO_1,
    "vision_design_check": VISION_SCENARIO_1,
    "feedback_consultation": FEEDBACK_SCENARIO_1,
}


def get_scenario(scenario_id: str) -> Dict[str, Any]:
    """Get golden output scenario by ID"""
    return GOLDEN_OUTPUTS.get(scenario_id)


def get_all_scenarios() -> List[Dict[str, Any]]:
    """Get all golden output scenarios"""
    return list(GOLDEN_OUTPUTS.values())


def get_scenarios_by_module(module: str) -> List[Dict[str, Any]]:
    """Get all scenarios for a specific module"""
    return [s for s in GOLDEN_OUTPUTS.values() if s["module"] == module]


def validate_output_against_golden(
    actual_panels: List[Dict[str, Any]],
    golden_scenario: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate actual output against golden scenario
    
    Returns:
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str],
            "panel_count_match": bool,
            "missing_panels": List[str],
            "extra_panels": List[str],
        }
    """
    errors = []
    warnings = []
    
    expected = golden_scenario["expected_panels"]
    expected_types = [p["type"] for p in expected]
    actual_types = [p["type"] for p in actual_panels]
    
    # Check panel types
    missing = set(expected_types) - set(actual_types)
    extra = set(actual_types) - set(expected_types)
    
    if missing:
        errors.append(f"Missing expected panels: {', '.join(missing)}")
    
    if extra:
        warnings.append(f"Extra panels (not in golden): {', '.join(extra)}")
    
    # Validate each panel's fields
    for exp_panel in expected:
        panel_type = exp_panel["type"]
        actual_panel = next((p for p in actual_panels if p["type"] == panel_type), None)
        
        if not actual_panel:
            continue  # Already reported as missing
        
        # Check required fields
        for field in exp_panel.get("required_fields", []):
            if field not in actual_panel.get("data", {}):
                errors.append(f"Panel {panel_type} missing required field: {field}")
        
        # Check minimum counts
        data = actual_panel.get("data", {})
        if "policies_min" in exp_panel:
            policy_count = len(data.get("policies", []))
            if policy_count < exp_panel["policies_min"]:
                errors.append(
                    f"Panel {panel_type} has {policy_count} policies, "
                    f"expected at least {exp_panel['policies_min']}"
                )
        
        if "issues_min" in exp_panel:
            issue_count = len(data.get("issues", []))
            if issue_count < exp_panel["issues_min"]:
                errors.append(
                    f"Panel {panel_type} has {issue_count} issues, "
                    f"expected at least {exp_panel['issues_min']}"
                )
        
        if "cases_min" in exp_panel:
            case_count = len(data.get("cases", []))
            if case_count < exp_panel["cases_min"]:
                errors.append(
                    f"Panel {panel_type} has {case_count} cases, "
                    f"expected at least {exp_panel['cases_min']}"
                )
        
        if "themes_min" in exp_panel:
            theme_count = len(data.get("themes", []))
            if theme_count < exp_panel["themes_min"]:
                errors.append(
                    f"Panel {panel_type} has {theme_count} themes, "
                    f"expected at least {exp_panel['themes_min']}"
                )
        
        if "scenarios_min" in exp_panel:
            scenario_count = len(data.get("scenarios", []))
            if scenario_count < exp_panel["scenarios_min"]:
                errors.append(
                    f"Panel {panel_type} has {scenario_count} scenarios, "
                    f"expected at least {exp_panel['scenarios_min']}"
                )
        
        if "constraints_min" in exp_panel:
            constraint_count = len(data.get("constraints", []))
            if constraint_count < exp_panel["constraints_min"]:
                errors.append(
                    f"Panel {panel_type} has {constraint_count} constraints, "
                    f"expected at least {exp_panel['constraints_min']}"
                )
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "panel_count_match": len(actual_types) == len(expected_types),
        "missing_panels": list(missing),
        "extra_panels": list(extra),
    }
