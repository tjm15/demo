"""LLM integration utilities.

Supports streaming text generation via Ollama and a simple VLM image analysis helper.
Falls back to a template text if provider is misconfigured or unavailable.
"""
from __future__ import annotations

import os
import asyncio
import json
import base64
from typing import AsyncGenerator, Optional

import aiohttp


OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
TEXT_MODEL = os.getenv("LLM_MODEL", os.getenv("LLM_MODEL_TEXT", "gpt-oss:20b"))
VLM_MODEL = os.getenv("LLM_MODEL_VLM", "qwen3-vl:30b")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
# Emergency bypass for testing when Ollama is stuck
DISABLE_LLM = os.getenv("DISABLE_LLM", "false").lower() == "true"


async def _ollama_stream_generate(prompt: str, model: Optional[str] = None) -> AsyncGenerator[str, None]:
    """Stream tokens from Ollama /api/generate. Yields partial text segments."""
    m = model or TEXT_MODEL
    url = f"{OLLAMA_BASE}/api/generate"
    payload = {
        "model": m,
        "prompt": prompt,
        "stream": True,
        # Keep defaults for now; users can tune via model params if needed
    }
    # Short connection timeout to fail fast if Ollama isn't running
    # Longer total timeout for generation
    timeout = aiohttp.ClientTimeout(total=120, connect=3)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload) as resp:
            resp.raise_for_status()
            async for raw in resp.content:
                if not raw:
                    continue
                # Ollama streams JSON lines
                try:
                    data = json.loads(raw.decode("utf-8"))
                except Exception:
                    continue
                chunk = data.get("response")
                if chunk:
                    yield chunk


async def stream_text(prompt: str) -> AsyncGenerator[str, None]:
    """Provider-agnostic streaming for text reasoning. Currently Ollama-focused."""
    # Emergency bypass
    if DISABLE_LLM:
        text = (
            "🔧 LLM DISABLED (DISABLE_LLM=true)\n\n"
            "This is a test fallback response to verify the rest of the system works.\n\n"
            f"**Module request:** {prompt[:200]}...\n\n"
            "The reasoning flow, panel emission, and citations should still function.\n"
        )
        for token in text.split():
            yield token + " "
            await asyncio.sleep(0.01)
        return
    
    provider = LLM_PROVIDER
    if provider == "ollama":
        try:
            async for piece in _ollama_stream_generate(prompt, TEXT_MODEL):
                yield piece
            return
        except Exception as e:
            # Log error and fall through to template fallback
            print(f"[LLM] Ollama streaming failed: {e}")
            pass

    # Fallback: yield template text demonstrating reasoning structure
    text = (
        "⚠️ LLM service unavailable (check Ollama). Using fallback template.\n\n"
        "## Analysis Framework\n\n"
        "This would normally contain live reasoning from the LLM, but the service is not connected.\n\n"
        f"**User request:** {prompt[:200]}...\n\n"
        "To enable live reasoning:\n"
        "1. Start Ollama: `ollama serve`\n"
        "2. Pull model: `ollama pull gpt-oss:20b`\n"
        "3. Restart kernel\n"
    )
    for token in text.split():
        yield token + " "
        await asyncio.sleep(0.01)


async def generate_text(prompt: str, model: Optional[str] = None) -> str:
    """Non-streamed text generation via Ollama (or fallback)."""
    provider = LLM_PROVIDER
    if provider == "ollama":
        m = model or TEXT_MODEL
        url = f"{OLLAMA_BASE}/api/generate"
        payload = {"model": m, "prompt": prompt, "stream": False}
        timeout = aiohttp.ClientTimeout(total=180, connect=3)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    return data.get("response", "")
        except Exception as e:
            print(f"[LLM] Ollama generation failed: {e}")
            pass
    # Fallback
    return "⚠️ LLM service unavailable. Start Ollama with: ollama serve"

async def analyze_image(image_bytes: bytes, prompt: Optional[str] = None) -> str:
    """Analyze an image using the configured VLM model on Ollama.
    Returns a single consolidated string response.
    """
    if LLM_PROVIDER != "ollama":
        return "VLM not configured; set LLM_PROVIDER=ollama and OLLAMA_BASE_URL."

    url = f"{OLLAMA_BASE}/api/generate"
    b64 = base64.b64encode(image_bytes).decode("ascii")
    final_prompt = prompt or "Describe the image and identify planning-relevant features (mass, height, materials, context)."
    payload = {
        "model": VLM_MODEL,
        "prompt": final_prompt,
        "images": [b64],
        "stream": False,
    }
    timeout = aiohttp.ClientTimeout(total=120, connect=3)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
                # Non-streaming returns a single object with 'response'
                return data.get("response", "")
    except Exception as e:
        return f"⚠️ VLM analysis failed: {e}. Ensure Ollama is running with model {VLM_MODEL}"


def build_system_prompt(module: str) -> str:
    """Return a compact system prompt tailored to the module."""
    base = (
        "You are The Planner's Assistant. Provide concise, grounded reasoning. "
        "Prefer bullet points. Avoid hallucinating citations."
    )
    mod_lines = {
        "dm": "Focus on material considerations, applicable policies, and a balanced recommendation.",
        "policy": "Review drafting clarity, consistency, and cross-references.",
        "strategy": "Compare options, trade-offs, and delivery implications.",
        "vision": "Discuss design and visual impacts in plain language.",
        "feedback": "Cluster themes and summarize sentiments.",
        "evidence": "Summarize constraints and relevant evidence sources.",
    }
    return base + "\n" + mod_lines.get(module, "")


def build_user_prompt(module: str, user_text: str, site: Optional[dict] = None, proposal: Optional[dict] = None) -> str:
    def _fallback(o):
        try:
            # handle datetimes/paths minimally via string
            return str(o)
        except Exception:
            return "<unserializable>"
    parts = [f"Module: {module}", f"Question: {user_text}"]
    if site:
        parts.append(f"Site: {json.dumps(site, default=_fallback)}")
    if proposal:
        parts.append(f"Proposal: {json.dumps(proposal, default=_fallback)}")
    parts.append("Respond step-by-step with a short rationale then actionable outputs.")
    return "\n".join(parts)
