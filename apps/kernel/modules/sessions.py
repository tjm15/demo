"""
DEPRECATED: sessions.py

This module previously provided an in-memory SessionManager used to
coordinate interactive, blocking prompts. For Cloud Run (stateless)
deployments we moved to a non-blocking prompt pattern. The original
session manager has been removed; this file provides a minimal shim
to avoid import errors in older code, but it intentionally performs
no server-side session coordination.
"""
from typing import Dict, Any, Optional
import uuid
import asyncio


class _NoopSession:
    def __init__(self, module: str, context: Dict[str, Any]):
        self.session_id = str(uuid.uuid4())
        self.module = module
        self.context = context
        self.event_queue = asyncio.Queue()


class _NoopManager:
    def create_session(self, module: str, context: Dict[str, Any]) -> _NoopSession:
        return _NoopSession(module, context)

    def get_session(self, session_id: str) -> Optional[_NoopSession]:
        return None

    def submit_user_response(self, session_id: str, response: Dict[str, Any]) -> bool:
        return False


_manager = _NoopManager()


def get_session_manager():
    return _manager
