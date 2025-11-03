"""
Helper utilities for interactive prompts.

NOTE: For Cloud Run / stateless deployments we no longer block the
server waiting for user input. These helpers emit a prompt (when a
session/event queue is available) and return the provided default
immediately so reasoning can continue. The frontend may re-run the
reasoning request with clarified parameters when the user responds.
"""
from typing import Dict, Any, Optional, List
from modules.context import ContextPack
import asyncio


async def prompt_user(
    context: ContextPack,
    question: str,
    input_type: str = "text",
    options: Optional[List[Dict[str, Any]]] = None,
    default: Optional[Any] = None,
    timeout_seconds: int = 300
) -> Optional[Dict[str, Any]]:
    """
    Prompt the user for input during reasoning and wait for response.
    
    Args:
        context: Current reasoning context (must have session attached)
        question: Question to ask the user
        input_type: Type of input - "text", "select", "multiselect", "confirm", "number"
        options: List of options for select/multiselect (e.g., [{"value": "A", "label": "Option A"}])
        default: Default value if user times out
        timeout_seconds: How long to wait for response
    
    Returns:
        User's response dict or None if timeout/no session
    """
    # Build prompt payload
    prompt_payload = {
        "prompt_id": None,
        "question": question,
        "input_type": input_type,
        "options": options or [],
        "default": default,
        "context": {"module": context.module, "prompt_snippet": context.prompt[:100]}
    }

    # If a session with an event_queue exists, emit the prompt (non-blocking)
    try:
        sess = getattr(context, "session", None)
        if sess and hasattr(sess, "event_queue"):
            # best-effort emit; do not await a user response
            try:
                await sess.event_queue.put({"type": "prompt_user", "data": prompt_payload})
            except Exception:
                # swallow errors - prompt emission is best-effort
                pass
    except Exception:
        pass

    # Return default immediately (stateless behaviour)
    return {"value": default} if default is not None else None


async def confirm_action(
    context: ContextPack,
    action: str,
    details: Optional[str] = None,
    default: bool = True
) -> bool:
    """
    Ask user to confirm an action (yes/no).
    
    Args:
        context: Current reasoning context
        action: Action description
        details: Additional details about the action
        default: Default value if timeout
    
    Returns:
        True if user confirms, False otherwise
    """
    question = f"Confirm: {action}"
    if details:
        question += f"\n\n{details}"
    
    # Emit prompt and return default immediately
    resp = await prompt_user(context, question, input_type="confirm", default=default)
    if resp is None:
        return default
    return bool(resp.get("value", default))


async def select_option(
    context: ContextPack,
    question: str,
    options: List[Dict[str, Any]],
    default: Optional[str] = None
) -> Optional[str]:
    """
    Ask user to select one option from a list.
    
    Args:
        context: Current reasoning context
        question: Question to ask
        options: List of {"value": str, "label": str} dicts
        default: Default value if timeout
    
    Returns:
        Selected value or None
    """
    # Emit prompt and return default immediately
    resp = await prompt_user(context, question, input_type="select", options=options, default=default)
    if resp is None:
        return default
    return resp.get("value", default)


async def get_text_input(
    context: ContextPack,
    question: str,
    default: Optional[str] = None,
    placeholder: Optional[str] = None
) -> Optional[str]:
    """
    Ask user for text input.
    
    Args:
        context: Current reasoning context
        question: Question to ask
        default: Default value if timeout
        placeholder: Placeholder text for input
    
    Returns:
        User's text input or None
    """
    # Emit prompt and return default immediately
    resp = await prompt_user(context, question, input_type="text", default=default)
    if resp is None:
        return default
    return resp.get("value", default)
