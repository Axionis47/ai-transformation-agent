from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from core import run_manager
from core.events import EventType
from core.schemas import (
    AssumptionsDraft,
    BudgetState,
    EvidenceItem,
    Opportunity,
    ReasoningState,
    Run,
    RunStatus,
)
from engines.pitch.engine import PitchEngine
from services.trace import emit

router = APIRouter()

_ENGAGEMENTS_PATH = Path(__file__).parent.parent.parent / "data" / "wins_kb_seed" / "engagements.json"


def _load_engagement_lookup() -> dict[str, dict]:
    with open(_ENGAGEMENTS_PATH) as f:
        records = json.load(f)
    return {r["engagement_id"]: r for r in records}


@router.post("/runs/{run_id}/synthesize")
def synthesize(run_id: str) -> dict:
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if run.status != RunStatus.REASONING:
        raise HTTPException(status_code=409, detail=f"Run must be in REASONING status, got: {run.status.value}")
    state = run.reasoning_state
    if state is None or not state.completed:
        raise HTTPException(status_code=400, detail="Reasoning not completed. Call POST /answer until completed=true.")

    intake = run.company_intake
    if intake is None:
        raise HTTPException(status_code=400, detail="Company intake missing from run")

    lookup = _load_engagement_lookup()
    engine = PitchEngine(config=run.config_snapshot, engagement_lookup=lookup)

    assumptions = run.assumptions or AssumptionsDraft(assumptions=[], open_questions=[])
    field_coverage = state.field_coverage if state else {}

    opportunities = engine.synthesize(run_id, run.evidence, assumptions, intake, field_coverage)
    run_manager.store_opportunities(run_id, opportunities)
    run_manager.transition(run_id, RunStatus.SYNTHESIS)

    budget_state = run.budget_state or BudgetState()
    report = engine.compose_report(run_id, opportunities, run.evidence, state, intake, budget_state)
    run_manager.store_report(run_id, report)
    run_manager.transition(run_id, RunStatus.REPORT)

    tier_counts = {}
    for opp in opportunities:
        tier_counts[opp.tier.value] = tier_counts.get(opp.tier.value, 0) + 1

    return {
        "opportunities": [o.model_dump() for o in opportunities],
        "tier_counts": tier_counts,
    }


@router.post("/runs/{run_id}/publish", response_model=Run)
def publish(run_id: str) -> Run:
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if run.status != RunStatus.REPORT:
        raise HTTPException(status_code=409, detail=f"Run must be in REPORT status, got: {run.status.value}")
    run_manager.transition(run_id, RunStatus.PUBLISHED)
    emit(run_id, EventType.RUN_PUBLISHED, {"run_id": run_id})
    return run_manager.get_run(run_id)  # type: ignore[return-value]


@router.get("/runs/{run_id}/evidence")
def get_evidence(run_id: str) -> list[EvidenceItem]:
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return run.evidence


@router.get("/runs/{run_id}/report")
def get_report(run_id: str) -> dict:
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return run.report


@router.get("/runs/{run_id}/opportunities")
def get_opportunities(run_id: str) -> list[Opportunity]:
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return run.opportunities
