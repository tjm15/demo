"""Security Guardrails
Input validation, rate limiting, and safety checks for the reasoning engine.
"""
import re
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

# Rate limiting storage (in-memory, move to Redis for production)
_rate_limits: Dict[str, list] = defaultdict(list)

# Dangerous patterns to block
BLOCKED_PATTERNS = [
    r"<script",
    r"javascript:",
    r"on\w+\s*=",  # event handlers
    r"eval\s*\(",
    r"exec\s*\(",
    r"__import__",
    r"\.\.\/",  # path traversal
    r";\s*(drop|delete|truncate)\s+",  # SQL injection attempts
]

BLOCKED_REGEX = re.compile("|".join(BLOCKED_PATTERNS), re.IGNORECASE)


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input to prevent injection attacks.
    Returns cleaned text or raises ValueError if dangerous patterns detected.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    
    # Length check
    if len(text) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length} characters")
    
    # Check for blocked patterns
    if BLOCKED_REGEX.search(text):
        raise ValueError("Input contains potentially dangerous patterns")
    
    # Strip control characters (except newlines, tabs)
    cleaned = "".join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    return cleaned.strip()


def check_rate_limit(
    identifier: str,
    max_requests: int = 10,
    window_seconds: int = 60
) -> bool:
    """
    Check if request is within rate limit.
    Returns True if allowed, False if rate limit exceeded.
    """
    now = time.time()
    window_start = now - window_seconds
    
    # Clean old entries
    _rate_limits[identifier] = [
        ts for ts in _rate_limits[identifier]
        if ts > window_start
    ]
    
    # Check limit
    if len(_rate_limits[identifier]) >= max_requests:
        return False
    
    # Add current request
    _rate_limits[identifier].append(now)
    return True


def validate_module(module: str) -> bool:
    """Validate module name is allowed."""
    allowed_modules = {"evidence", "policy", "strategy", "vision", "feedback", "dm"}
    return module in allowed_modules


def validate_run_mode(mode: str) -> bool:
    """Validate run mode is allowed."""
    allowed_modes = {"stable", "deep"}
    return mode in allowed_modes


def validate_site_data(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate and sanitize site data.
    Returns cleaned data or raises ValueError.
    """
    if data is None:
        return {}
    
    if not isinstance(data, dict):
        raise ValueError("Site data must be a dictionary")
    
    # Validate lat/lng if present
    if "lat" in data:
        try:
            lat = float(data["lat"])
            if not (-90 <= lat <= 90):
                raise ValueError("Latitude must be between -90 and 90")
        except (TypeError, ValueError):
            raise ValueError("Invalid latitude value")
    
    if "lng" in data:
        try:
            lng = float(data["lng"])
            if not (-180 <= lng <= 180):
                raise ValueError("Longitude must be between -180 and 180")
        except (TypeError, ValueError):
            raise ValueError("Invalid longitude value")
    
    # Sanitize address field if present
    if "address" in data and isinstance(data["address"], str):
        data["address"] = sanitize_input(data["address"], max_length=500)
    
    return data


def validate_proposal_data(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate and sanitize proposal data.
    Returns cleaned data or raises ValueError.
    """
    if data is None:
        return {}
    
    if not isinstance(data, dict):
        raise ValueError("Proposal data must be a dictionary")
    
    # Validate numeric fields
    numeric_fields = ["units", "sqm", "height", "storeys"]
    for field in numeric_fields:
        if field in data:
            try:
                value = float(data[field])
                if value < 0:
                    raise ValueError(f"{field} cannot be negative")
                if value > 1000000:  # reasonable upper bound
                    raise ValueError(f"{field} exceeds reasonable maximum")
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid {field}: {e}")
    
    # Sanitize text fields
    text_fields = ["description", "use_class"]
    for field in text_fields:
        if field in data and isinstance(data[field], str):
            data[field] = sanitize_input(data[field], max_length=2000)
    
    return data


def validate_llm_output(output: str, max_tokens: int = 4000) -> str:
    """
    Validate LLM output for safety.
    Checks for excessive length, dangerous patterns, etc.
    """
    if not isinstance(output, str):
        raise ValueError("LLM output must be a string")
    
    # Token approximation (rough: 1 token ≈ 4 chars)
    approx_tokens = len(output) // 4
    if approx_tokens > max_tokens:
        # Truncate rather than fail
        output = output[:max_tokens * 4] + "... [truncated]"
    
    # Check for injection attempts in LLM output
    # (LLM might be manipulated to output dangerous content)
    if BLOCKED_REGEX.search(output):
        raise ValueError("LLM output contains potentially dangerous patterns")
    
    return output


def log_security_event(
    event_type: str,
    identifier: str,
    details: Dict[str, Any],
    severity: str = "info"
) -> None:
    """
    Log security-relevant events.
    In production, send to SIEM or security logging system.
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "identifier": identifier,
        "severity": severity,
        "details": details
    }
    
    # For now, just print (replace with proper logging in production)
    if severity in ["warning", "error"]:
        print(f"[SECURITY {severity.upper()}] {event_type}: {details}")


# Audit trail for sensitive operations
def audit_operation(
    operation: str,
    user_id: str,
    module: str,
    details: Dict[str, Any]
) -> None:
    """
    Audit sensitive operations for compliance.
    """
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "operation": operation,
        "user_id": user_id,
        "module": module,
        "details": details
    }
    
    # In production: write to append-only audit log
    print(f"[AUDIT] {operation} by {user_id} in {module}: {details}")
