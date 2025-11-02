"""Constraint synthesis service.

Endpoints:
- POST /synthesise → structured constraint list (JSON)
- POST /explain → rationale per item
"""
from __future__ import annotations
from typing import List, Dict, Any
import json

from fastapi import APIRouter

from contracts.schemas import (
    SynthesiseRequest,
    SynthesiseResponse,
    ConstraintItem,
    GraphContext,
    ExplainRequest,
    ExplainResponse,
    ExplainItem,
)
from .retriever import retrieve as retriever_endpoint

router = APIRouter()


def _classify_constraint(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["must", "required", "shall", "not exceed"]):
        return "requirement"
    if any(k in t for k in ["should", "encouraged", "seek to"]):
        return "advisory"
    if any(k in t for k in ["not permitted", "contrary", "refuse"]):
        return "conflict"
    return "advisory"


@router.post("/synthesise", response_model=SynthesiseResponse)
async def synthesise(req: SynthesiseRequest) -> SynthesiseResponse:
    # Use retriever to get ranked chunks
    ret = await retriever_endpoint(
        type("_R", (), {
            "question": req.question,
            "site_geom": req.site_geom,
            "lpa_code": req.lpa_code,
            "top_k": req.top_k,
        })
    )

    constraints: List[ConstraintItem] = []
    seen: set[tuple[str, str]] = set()

    for ch in ret.chunks:
        kind = _classify_constraint(ch.text)
        key = (kind, ch.para_ref or ch.chunk_id)
        if key in seen:
            continue
        seen.add(key)
        certainty = min(1.0, max(0.2, 0.6 * (ch.sim or 0.0) + 0.3 * (ch.bm25 or 0.0) + 0.1))
        why = []
        if ch.tags:
            why.append(f"site overlaps: {', '.join(ch.tags[:3])}")
        if ch.para_ref:
            why.append(f"clause {ch.para_ref}")
        why.append("relevant text match")
        constraints.append(ConstraintItem(
            type=kind,
            title=ch.policy_title or (ch.policy_id or "policy"),
            clause=ch.para_ref,
            source_policy=ch.policy_id,
            certainty=certainty,
            why="; ".join(why),
            refs=[ch.chunk_id],
        ))

    # Simple de-duplication by policy + clause, keep top per type
    dedup: Dict[str, ConstraintItem] = {}
    for c in constraints:
        key = f"{c.type}:{c.source_policy}:{c.clause}"
        if key not in dedup:
            dedup[key] = c
    constraints = list(dedup.values())
    # Trim per type theme (heuristic)
    constraints = constraints[: req.top_k]

    return SynthesiseResponse(constraints=constraints, graph=ret.graph)


@router.post("/explain", response_model=ExplainResponse)
async def explain(req: ExplainRequest) -> ExplainResponse:
    out: List[ExplainItem] = []
    for item in req.items:
        rationale = item.why or "Included due to site context and policy text match."
        if item.type == "conflict":
            rationale += " This appears to restrict the proposal based on the cited clause."
        elif item.type == "requirement":
            rationale += " This is a mandatory criterion officers typically expect to see addressed."
        else:
            rationale += " Considered advisory, informing design development."
        out.append(ExplainItem(item=item, rationale=rationale))
    return ExplainResponse(explanations=out)
