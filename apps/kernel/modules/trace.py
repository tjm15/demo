"""Trace logging for reasoning sessions."""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel

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
    with open(path, 'a') as f:
        f.write(entry.model_dump_json() + '\n')
