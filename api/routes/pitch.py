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
from services.memory.router import ContextRouter
from services.memory.store import get_evidence_store
from services.memory.opp_store import get_opportunity_store
from services.memory.report_store import get_report_store
from services.trace import emit

_router = ContextRouter()

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

    # Build grounder for LLM-based opportunity evaluation
    from services.grounder.grounder import Grounder
    from api.routes.grounding import _build_client
    client = _build_client(run.config_snapshot)
    grounder = Grounder(client=client, config=run.config_snapshot)

    engine = PitchEngine(config=run.config_snapshot, engagement_lookup=lookup, grounder=grounder)

    assumptions = run.assumptions or AssumptionsDraft(assumptions=[], open_questions=[])
    field_coverage = state.field_coverage if state else {}

    # Route context: pitch engine gets filtered evidence, not full blob
    pitch_ctx = _router.recall_for_pitch(
        run_id, get_evidence_store().get_all(run_id), assumptions, intake, field_coverage
    )
    opportunities = engine.synthesize(
        run_id, pitch_ctx.evidence, assumptions, intake, field_coverage
    )
    run_manager.store_opportunities(run_id, opportunities)
    run_manager.transition(run_id, RunStatus.SYNTHESIS)

    # Route context: report composer gets only linked evidence
    budget_state = run.budget_state or BudgetState()
    report_ctx = _router.recall_for_report(
        run_id, opportunities, get_evidence_store().get_all(run_id), intake, state, budget_state
    )
    report = engine.compose_report(
        run_id, opportunities, report_ctx.linked_evidence, state, intake, budget_state
    )
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
    return get_evidence_store().get_all(run_id)


@router.get("/runs/{run_id}/report")
def get_report(run_id: str) -> dict:
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return get_report_store().get(run_id)


@router.get("/runs/{run_id}/opportunities")
def get_opportunities(run_id: str) -> list[Opportunity]:
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return get_opportunity_store().get_all(run_id)
