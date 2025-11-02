"""
Patch emission helpers for kernel
Convert internal panel generation to validated patch operations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
sys.path.append('/home/tjm/code/demo')

from contracts.schemas import (
    PanelData,
    PatchOperation,
    PatchEnvelope,
    PatchOp,
    Module,
    validate_panel_data,
)
from contracts.id_generator import generate_panel_id_from_data


def create_show_panel_intent(
    panel_type: str,
    data: Dict[str, Any],
    module: str,
    panel_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a show_panel intent (legacy format for backward compatibility)
    This will be translated to patch ops on the frontend
    """
    # Generate deterministic ID if not provided
    if not panel_id:
        panel_id = generate_panel_id_from_data(panel_type, data)
    
    return {
        "action": "show_panel",
        "panel": panel_type,
        "id": panel_id,
        "data": data,
    }


def create_patch_envelope(
    ops: List[Dict[str, Any]],
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a patch envelope with operations
    """
    # Validate each operation
    validated_ops = []
    for op_dict in ops:
        try:
            op = PatchOperation(**op_dict)
            validated_ops.append(op.dict(by_alias=True))
        except Exception as e:
            print(f"Warning: Invalid patch operation: {e}")
            continue
    
    envelope = {
        "action": "patch",
        "ops": validated_ops,
    }
    
    if session_id:
        envelope["session_id"] = session_id
    
    return envelope


def create_add_panel_op(
    panel_type: str,
    data: Dict[str, Any],
    module: str,
    panel_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an 'add' patch operation to append a new panel
    """
    # Validate panel data
    is_valid, error = validate_panel_data(panel_type, data)
    if not is_valid:
        raise ValueError(f"Invalid panel data for {panel_type}: {error}")
    
    # Generate deterministic ID
    if not panel_id:
        panel_id = generate_panel_id_from_data(panel_type, data)
    
    # Create panel object
    panel = {
        "id": panel_id,
        "type": panel_type,
        "data": data,
        "timestamp": int(datetime.utcnow().timestamp() * 1000),
        "module": module,
    }
    
    # Create add operation (append to end)
    return {
        "op": "add",
        "path": "/panels/-",
        "value": panel,
    }


def emit_panel_as_intent(
    panel_type: str,
    data: Dict[str, Any],
    module: str,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Emit panel as intent event (for SSE streaming)
    Frontend will translate to patch
    """
    return {
        "type": "intent",
        "data": create_show_panel_intent(panel_type, data, module)
    }


def emit_panel_as_patch(
    panel_type: str,
    data: Dict[str, Any],
    module: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Emit panel as patch event (for SSE streaming)
    Frontend will apply directly
    """
    try:
        op = create_add_panel_op(panel_type, data, module)
        envelope = create_patch_envelope([op], session_id)
        
        return {
            "type": "patch",
            "data": envelope
        }
    except ValueError as e:
        # Validation failed, emit error
        return {
            "type": "error",
            "data": {
                "message": f"Panel validation failed: {e}",
                "panel_type": panel_type,
            }
        }


def create_safe_mode_panel(
    reason: str,
    error_count: int = 0
) -> Dict[str, Any]:
    """
    Create a safe mode notice panel
    """
    return {
        "id": "safe_mode_notice",
        "type": "safe_mode_notice",
        "data": {
            "reason": reason,
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "errorCount": error_count,
            "message": "The system entered safe mode due to validation errors."
        },
        "timestamp": int(datetime.utcnow().timestamp() * 1000),
    }


# Budget limits per run mode (should match TypeScript registry)
BUDGET_LIMITS = {
    "stable": {
        "max_panels": 5,
        "max_weight": 12,
    },
    "deep": {
        "max_panels": 15,
        "max_weight": 40,
    }
}


# Panel weights (should match TypeScript registry)
PANEL_WEIGHTS = {
    "applicable_policies": 2,
    "key_issues_matrix": 3,
    "precedents": 2,
    "planning_balance": 3,
    "draft_decision": 4,
    "evidence_snapshot": 2,
    "policy_editor": 3,
    "conflict_heatmap": 2,
    "scenario_compare": 4,
    "visual_compliance": 3,
    "consultation_themes": 2,
    "map": 3,
    "doc_viewer": 1,
}


class BudgetTracker:
    """Track panel budget for run mode"""
    
    def __init__(self, run_mode: str = "stable"):
        self.run_mode = run_mode
        self.panel_count = 0
        self.total_weight = 0
        self.limits = BUDGET_LIMITS.get(run_mode, BUDGET_LIMITS["stable"])
    
    def can_add_panel(self, panel_type: str) -> tuple[bool, Optional[str]]:
        """Check if panel can be added within budget"""
        weight = PANEL_WEIGHTS.get(panel_type, 1)
        
        if self.panel_count >= self.limits["max_panels"]:
            return False, f"Panel limit reached ({self.limits['max_panels']})"
        
        if self.total_weight + weight > self.limits["max_weight"]:
            return False, f"Weight budget exceeded ({self.limits['max_weight']})"
        
        return True, None
    
    def add_panel(self, panel_type: str):
        """Record panel addition"""
        weight = PANEL_WEIGHTS.get(panel_type, 1)
        self.panel_count += 1
        self.total_weight += weight
