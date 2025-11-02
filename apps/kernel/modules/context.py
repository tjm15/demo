"""Context and request models for reasoning kernel."""
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel

class ReasonRequest(BaseModel):
    module: Literal["evidence", "policy", "strategy", "vision", "feedback", "dm"]
    prompt: str
    site_data: Optional[Dict[str, Any]] = None
    proposal_data: Optional[Dict[str, Any]] = None
    run_mode: Literal["stable", "deep"] = "stable"
    allow_web_fetch: bool = False
    # When true, kernel suggests actions and does NOT auto-execute them
    interactive_actions: bool = True

class ContextPack(BaseModel):
    """Context bundle for reasoning."""
    module: str
    prompt: str
    site_data: Optional[Dict[str, Any]] = None
    proposal_data: Optional[Dict[str, Any]] = None
    run_mode: str = "stable"
    allow_web_fetch: bool = False
    interactive_actions: bool = True
    
    def get_tool_budget(self) -> int:
        """Get tool call budget based on run mode."""
        return 5 if self.run_mode == "stable" else 15
    
    def get_web_fetch_limit(self) -> int:
        """Get web fetch limit based on run mode."""
        if not self.allow_web_fetch:
            return 0
        return 1 if self.run_mode == "stable" else 3
