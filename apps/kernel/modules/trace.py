"""Trace logging for reasoning sessions."""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, date


def _json_default(obj):
    """Best-effort serializer for trace payloads."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    try:
        return obj.__json__()  # type: ignore[attr-defined]
    except Exception:
        return str(obj)

class TraceEntry(BaseModel):
    """Single trace entry."""
    t: str  # ISO timestamp
    step: str
    module: Optional[str] = None
    tool: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    output: Optional[Any] = None
    ms: Optional[int] = None
    error: Optional[str] = None

async def write_trace(path: Path, entry: TraceEntry):
    """Append trace entry to JSONL file."""
    line = None
    try:
        line = entry.model_dump_json()
    except Exception:
        try:
            # Fallback to generic json.dumps with default handler
            line = json.dumps(entry.model_dump(), default=_json_default)
        except Exception:
            # Final fallback: minimal fields only
            minimal = {
                "t": getattr(entry, 't', ''),
                "step": getattr(entry, 'step', ''),
                "module": getattr(entry, 'module', None),
                "error": "trace_serialize_failed"
            }
            line = json.dumps(minimal)
    with open(path, 'a') as f:
        f.write(line + '\n')
