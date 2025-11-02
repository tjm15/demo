from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import json
from typing import Literal, Optional

router = APIRouter()

Module = Literal['evidence', 'policy', 'strategy', 'vision', 'feedback', 'dm']


class ClassifyRequest(BaseModel):
    prompt: str


class ClassifyResponse(BaseModel):
    module: Module
    source: Literal['llm', 'heuristic']
    confidence: float


def _heuristic_classify(text: str) -> Module:
    t = text.lower()
    score = {m: 0 for m in ['evidence', 'policy', 'strategy', 'vision', 'feedback', 'dm']}

    def bump(m: str, n: int = 1):
        score[m] += n

    # Evidence / DM
    import re
    if re.search(r"\b(lat|latitude)[^\d-]*[-+]?\d|\b(lon|lng|longitude)[^\d-]*[-+]?\d", t):
        bump('evidence', 2); bump('dm', 2)
    if re.search(r"(site|parcel|plot|map|constraints|flood|heritage|conservation|brownfield)", t):
        bump('evidence', 2); bump('dm', 1)
    if re.search(r"(units|storeys|stories|dwellings|application|app ref|planning ref)", t):
        bump('dm', 2)

    # Policy
    if re.search(r"(policy|draft|wording|criterion|compliance|soundness|h\d+\.?\d*|london plan|nppf|npff)", t):
        bump('policy', 3)

    # Strategy
    if re.search(r"(scenario|compare|vs\.|versus|option|model|impact|capacity|5000 homes|targets|trajectory)", t):
        bump('strategy', 3)

    # Vision
    if re.search(r"(render|visual|concept|design|façade|facade|materials|mass\b|elevation|streetscape|illustration)", t):
        bump('vision', 3)

    # Feedback
    if re.search(r"(consultation|responses|objections|themes|survey|sentiment|feedback|comments)", t):
        bump('feedback', 3)

    if re.search(r"(where|what|show|find|nearby|around)", t):
        bump('evidence', 1)

    order = ['dm', 'evidence', 'policy', 'strategy', 'feedback', 'vision']
    best = 'evidence'
    best_score = -10
    for m in order:
        if score[m] > best_score:
            best, best_score = m, score[m]
    return best  # type: ignore


def _classify_with_llm(prompt: str) -> Optional[Module]:
    provider = os.getenv('LLM_PROVIDER', '').lower()
    model = os.getenv('LLM_MODEL', '')
    if not provider or not model:
        return None

    system = (
        "You classify planning questions into one of these modules: "
        "['evidence','policy','strategy','vision','feedback','dm']. "
        "Return ONLY a compact JSON object: {\"module\": <one of the labels>}. "
        "Choose 'dm' for site/application-specific assessment, 'evidence' for data/constraints/doc retrieval, "
        "'policy' for drafting/checking policy wording, 'strategy' for scenarios/comparisons/targets, "
        "'vision' for design/visual/massing/facade topics, 'feedback' for consultation themes."
    )

    try:
        if provider == 'openai':
            try:
                from openai import OpenAI  # type: ignore
            except Exception:
                return None
            client = OpenAI()
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                response_format={"type": "json_object"},
                max_tokens=20,
            )
            content = resp.choices[0].message.content or "{}"
            data = json.loads(content)
            m = data.get('module')
            if m in ['evidence', 'policy', 'strategy', 'vision', 'feedback', 'dm']:
                return m  # type: ignore
            return None

        if provider == 'anthropic':
            try:
                import anthropic  # type: ignore
            except Exception:
                return None
            client = anthropic.Anthropic()
            msg = client.messages.create(
                model=model,
                max_tokens=50,
                temperature=0,
                messages=[
                    {"role": "user", "content": f"SYSTEM:\n{system}\n\nUSER:\n{prompt}"}
                ],
            )
            # Anthropic SDK returns content blocks
            text = ''.join([blk.text for blk in msg.content if getattr(blk, 'type', '') == 'text'])
            try:
                data = json.loads(text)
                m = data.get('module')
                if m in ['evidence', 'policy', 'strategy', 'vision', 'feedback', 'dm']:
                    return m  # type: ignore
            except Exception:
                return None
            return None
    except Exception:
        return None

    return None


@router.post("/classify", response_model=ClassifyResponse)
async def classify(req: ClassifyRequest) -> ClassifyResponse:
    text = (req.prompt or '').strip()
    if not text:
        raise HTTPException(status_code=400, detail="prompt is required")

    m = _classify_with_llm(text)
    if m:
        return ClassifyResponse(module=m, source='llm', confidence=0.9)

    # fallback
    m2 = _heuristic_classify(text)
    return ClassifyResponse(module=m2, source='heuristic', confidence=0.6)
