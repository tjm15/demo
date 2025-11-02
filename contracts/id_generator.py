"""
Deterministic ID generation for panels (Python version)
Mirrors the TypeScript id-generator.ts implementation
"""

import hashlib
from typing import Optional, Dict, Any, List


def hash_string(s: str) -> str:
    """
    Generate a short hash from a string
    Uses MD5 for consistency (not for security)
    """
    return hashlib.md5(s.encode('utf-8')).hexdigest()[:8]


def generate_panel_id(
    panel_type: str,
    content_key: Optional[str] = None,
    index: Optional[int] = None
) -> str:
    """
    Generate a stable panel ID from type and content
    
    Args:
        panel_type: The panel type (e.g., "applicable_policies")
        content_key: Optional content key for differentiation
        index: Optional index for multiple instances
        
    Returns:
        Deterministic panel ID
        
    Examples:
        >>> generate_panel_id("applicable_policies")
        'applicable_policies'
        
        >>> generate_panel_id("precedents", "appeal_case_123")
        'precedents_3k7m9p2q'
        
        >>> generate_panel_id("doc_viewer", "LP_2024", 1)
        'doc_viewer_5a8b3c2d_1'
    """
    # For single-instance panels without content differentiation
    if not content_key and index is None:
        return panel_type
    
    # For panels with content key, hash it for stable suffix
    if content_key:
        content_hash = hash_string(content_key)
        base = f"{panel_type}_{content_hash}"
        return f"{base}_{index}" if index is not None else base
    
    # For indexed panels without content key
    return f"{panel_type}_{index}"


def extract_content_key(panel_type: str, data: Dict[str, Any]) -> Optional[str]:
    """
    Extract content key from panel data for ID generation
    Inspects panel data to find a stable identifier
    """
    if not data or not isinstance(data, dict):
        return None
    
    if panel_type == "applicable_policies":
        # Hash the policy IDs
        if "policies" in data and isinstance(data["policies"], list):
            ids = sorted([p.get("id") for p in data["policies"] if p.get("id")])
            return ",".join(ids) if ids else None
    
    elif panel_type == "precedents":
        # Hash the case refs
        if "cases" in data and isinstance(data["cases"], list):
            refs = sorted([c.get("ref") for c in data["cases"] if c.get("ref")])
            return ",".join(refs) if refs else None
    
    elif panel_type == "doc_viewer":
        # Use doc_id directly
        return data.get("doc_id")
    
    elif panel_type == "policy_editor":
        # Use policy_id
        return data.get("policy_id")
    
    elif panel_type == "scenario_compare":
        # Hash scenario IDs
        if "scenarios" in data and isinstance(data["scenarios"], list):
            ids = sorted([s.get("id") for s in data["scenarios"] if s.get("id")])
            return "_vs_".join(ids) if ids else None
    
    elif panel_type == "map":
        # Use center coordinates as key
        center = data.get("center")
        if center and isinstance(center, dict):
            lat = center.get("lat")
            lng = center.get("lng")
            if lat is not None and lng is not None:
                return f"{lat:.4f},{lng:.4f}"
    
    elif panel_type == "evidence_snapshot":
        # Use site location if available
        site = data.get("site")
        if site and isinstance(site, dict):
            lat = site.get("lat")
            lng = site.get("lng")
            if lat is not None and lng is not None:
                return f"{lat:.4f},{lng:.4f}"
    
    return None


def generate_panel_id_from_data(
    panel_type: str,
    data: Dict[str, Any],
    index: Optional[int] = None
) -> str:
    """
    Generate panel ID with automatic content key extraction
    """
    content_key = extract_content_key(panel_type, data)
    return generate_panel_id(panel_type, content_key, index)


def matches_panel_id(
    panel_id: str,
    panel_type: str,
    content_key: Optional[str] = None
) -> bool:
    """
    Check if a panel ID matches a type and optional content
    """
    expected_id = generate_panel_id(panel_type, content_key)
    return panel_id == expected_id or panel_id.startswith(f"{expected_id}_")


def get_panel_type_from_id(panel_id: str) -> str:
    """
    Parse panel type from ID
    ID format: "type" or "type_hash" or "type_hash_index"
    """
    parts = panel_id.split('_')
    
    # Handle compound types like "key_issues_matrix"
    # Simple heuristic: if last part is numeric or short hash, exclude it
    if len(parts) > 1:
        last = parts[-1]
        # If last part looks like index or hash, exclude it
        if last.isdigit() or (len(last) == 8 and all(c in '0123456789abcdef' for c in last)):
            return '_'.join(parts[:-1])
    
    return parts[0] if parts else panel_id
