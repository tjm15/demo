"""
Reasoning Kernel for The Planner's Assistant
Provides streaming reasoning with module-aware security.
"""
import os
import sys
import json
import asyncio
from uuid import uuid4
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, List, Optional

# Add repo root to Python path so we can import from contracts/
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from modules.context import ContextPack, ReasonRequest
from modules.playbook import execute_playbook
from modules.trace import TraceEntry, write_trace

app = FastAPI(title="TPA Reasoning Kernel")

# CORS for frontend
# CORS: allow all localhost/127.0.0.1 origins for dev
import re
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
# Default to local logs directory for dev; can override with LOG_DIR env var
LOG_DIR = Path(os.getenv("LOG_DIR", "./logs/traces"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Health check
@app.get("/status")
async def status():
    return {"status": "ok", "service": "tpa-kernel"}

# Main reasoning endpoint
@app.post("/reason")
async def reason(req: ReasonRequest):
    """Stream reasoning process with intents and tokens."""
    
    async def event_generator() -> AsyncGenerator[Dict[str, Any], None]:
        session_id = str(uuid4())
        trace_path = LOG_DIR / f"{session_id}.jsonl"
        
        try:
            # Security validation
            from modules.security import (
                sanitize_input, check_rate_limit, validate_module,
                validate_run_mode, validate_site_data, validate_proposal_data,
                log_security_event
            )
            
            # Rate limiting (by IP or user ID in production)
            client_id = f"session_{session_id}"  # Replace with real user ID
            if not check_rate_limit(client_id, max_requests=20, window_seconds=60):
                log_security_event("rate_limit_exceeded", client_id, {"module": req.module}, "warning")
                yield {
                    "event": "error",
                    "data": json.dumps({"message": "Rate limit exceeded. Please try again later."})
                }
                return
            
            # Input validation
            try:
                req.prompt = sanitize_input(req.prompt, max_length=5000)
                if not validate_module(req.module):
                    raise ValueError(f"Invalid module: {req.module}")
                if not validate_run_mode(req.run_mode):
                    raise ValueError(f"Invalid run mode: {req.run_mode}")
                if req.site_data:
                    req.site_data = validate_site_data(req.site_data)
                if req.proposal_data:
                    req.proposal_data = validate_proposal_data(req.proposal_data)
            except ValueError as e:
                log_security_event("input_validation_failed", client_id, {"error": str(e)}, "warning")
                yield {
                    "event": "error",
                    "data": json.dumps({"message": f"Invalid input: {e}"})
                }
                return
            
            # Build context pack
            context = ContextPack(
                module=req.module,
                prompt=req.prompt,
                site_data=req.site_data,
                proposal_data=req.proposal_data,
                run_mode=req.run_mode,
                allow_web_fetch=req.allow_web_fetch
            )
            
            # Log start
            await write_trace(trace_path, TraceEntry(
                t=datetime.utcnow().isoformat(),
                step="init",
                module=req.module,
                input={"prompt": req.prompt[:100], "session_id": session_id}
            ))
            
            # Execute playbook
            async for event in execute_playbook(context, trace_path):
                yield {
                    "event": event["type"],
                    "data": json.dumps(event["data"])
                }
            
            # Log completion
            await write_trace(trace_path, TraceEntry(
                t=datetime.utcnow().isoformat(),
                step="complete",
                module=req.module
            ))
            
        except Exception as e:
            log_security_event("reasoning_error", session_id, {"error": str(e)}, "error")
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)})
            }
    
    return EventSourceResponse(event_generator())

# Service endpoints (called by playbook tools)
from services import policy, docs, spatial, precedent, standards, feedback, classify
from services import retriever as retriever_service
from services import synthesise as synthesise_service
from services import map_overlays as map_overlays_service
from services import files as files_service
from services import ingest as ingest_service
from services import actions as actions_service
from services import evidence as evidence_service

app.include_router(policy.router, prefix="/services/policy", tags=["policy"])
app.include_router(docs.router, prefix="/services/docs", tags=["docs"])
app.include_router(spatial.router, prefix="/services/spatial", tags=["spatial"])
app.include_router(precedent.router, prefix="/services/precedent", tags=["precedent"])
app.include_router(standards.router, prefix="/services/standards", tags=["standards"])
app.include_router(feedback.router, prefix="/services/feedback", tags=["feedback"])
app.include_router(classify.router, prefix="/services", tags=["classify"])
app.include_router(files_service.router, prefix="/services/files", tags=["files"])
app.include_router(ingest_service.router, prefix="/services/ingest", tags=["ingest"])
app.include_router(actions_service.router, prefix="/services", tags=["actions"])
app.include_router(evidence_service.router, prefix="/evidence", tags=["evidence"])

# New Planner-pattern endpoints
app.include_router(retriever_service.router, tags=["retrieval"])
app.include_router(synthesise_service.router, tags=["synthesis"])
app.include_router(map_overlays_service.router, tags=["map"])

if __name__ == "__main__":
    import uvicorn
    # Run without reload when executed directly (for background processes)
    # Reload mode should be used via: uvicorn main:app --reload
    uvicorn.run(app, host="127.0.0.1", port=8081, log_level="info")

