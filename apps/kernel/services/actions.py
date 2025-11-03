from typing import Optional, Dict, Any, Literal, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.context import ContextPack
from modules.reasoning_executor import execute_actions, extract_actions

router = APIRouter(prefix="/actions", tags=["actions"])


class ExecuteActionRequest(BaseModel):
    module: Literal["evidence", "policy", "strategy", "vision", "feedback", "dm"]
    action: str
    prompt: Optional[str] = ""
    site_data: Optional[Dict[str, Any]] = None
    proposal_data: Optional[Dict[str, Any]] = None
    query: Optional[str] = None


@router.post("/execute")
async def execute_action(req: ExecuteActionRequest) -> Dict[str, Any]:
    ctx = ContextPack(
        module=req.module,
        prompt=req.prompt or "",
        site_data=req.site_data,
        proposal_data=req.proposal_data,
        run_mode="stable",
        allow_web_fetch=False,
        interactive_actions=True,
    )

    intents = await execute_actions([
        {"type": req.action, "query": req.query}
    ], ctx, citations=[])

    # Return intents in the same shape as SSE intent data (without event wrapper)
    return {
        "intents": [i.get("data") for i in intents if i.get("type") == "intent"]
    }


class SuggestActionsRequest(BaseModel):
    module: Literal["evidence", "policy", "strategy", "vision", "feedback", "dm"]
    reasoning_text: str


@router.post("/suggest")
async def suggest_actions(req: SuggestActionsRequest) -> Dict[str, Any]:
    actions = extract_actions(req.reasoning_text or "", req.module)
    return {"suggestions": actions}
