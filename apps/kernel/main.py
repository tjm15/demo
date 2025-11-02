"""
Reasoning Kernel for The Planner's Assistant
Provides streaming reasoning with module-aware security.
"""
import os
import json
import asyncio
from uuid import uuid4
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from modules.context import ContextPack, ReasonRequest
from modules.playbook import execute_playbook
from modules.trace import TraceEntry, write_trace

app = FastAPI(title="TPA Reasoning Kernel")

# CORS for frontend
# CORS: allow common local dev origins (Vite defaults + custom)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
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
                input={"prompt": req.prompt[:100]}
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
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)})
            }
    
    return EventSourceResponse(event_generator())

# Service endpoints (called by playbook tools)
from services import policy, docs, spatial, precedent, standards, feedback, classify
from services import files as files_service
from services import ingest as ingest_service

app.include_router(policy.router, prefix="/services/policy", tags=["policy"])
app.include_router(docs.router, prefix="/services/docs", tags=["docs"])
app.include_router(spatial.router, prefix="/services/spatial", tags=["spatial"])
app.include_router(precedent.router, prefix="/services/precedent", tags=["precedent"])
app.include_router(standards.router, prefix="/services/standards", tags=["standards"])
app.include_router(feedback.router, prefix="/services/feedback", tags=["feedback"])
app.include_router(classify.router, prefix="/services", tags=["classify"])
app.include_router(files_service.router, prefix="/services/files", tags=["files"])
app.include_router(ingest_service.router, prefix="/services/ingest", tags=["ingest"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8081, reload=True)
