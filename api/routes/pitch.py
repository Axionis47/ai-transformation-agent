from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from core import run_manager
from core.events import EventType
from core.schemas import (
    Assumption,
    AssumptionsDraft,
    BudgetState,
    EvidenceItem,
    Opportunity,
    ReasoningState,
    RefineRequest,
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
        run_id, opportunities, report_ctx.linked_evidence, state, intake, budget_state,
        assumptions=run.assumptions,
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


@router.post("/runs/{run_id}/refine")
def refine_report(run_id: str, body: RefineRequest) -> dict:
    """Apply corrections and re-score opportunities without re-running full pipeline."""
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if run.status not in (RunStatus.REPORT, RunStatus.PUBLISHED):
        raise HTTPException(status_code=409, detail=f"Run must be in REPORT or PUBLISHED status")

    changes: dict = {"corrected": [], "removed": []}

    # Apply assumption corrections
    if body.corrections and run.assumptions:
        for corr in body.corrections:
            for a in run.assumptions.assumptions:
                if a.field == corr.field:
                    changes["corrected"].append({"field": corr.field, "old": a.value, "new": corr.new_value})
                    a.value = corr.new_value
                    a.confidence = 1.0
                    a.source = "user"
        run_manager.update_assumptions(run_id, run.assumptions)
        emit(run_id, EventType.ASSUMPTIONS_CORRECTED, {"corrections": changes["corrected"]})

    # Remove opportunities
    if body.removed_opportunity_ids:
        kept = [o for o in run.opportunities if o.opportunity_id not in body.removed_opportunity_ids]
        changes["removed"] = body.removed_opportunity_ids
        run_manager.store_opportunities(run_id, kept)
        emit(run_id, EventType.OPPORTUNITIES_REMOVED, {"ids": body.removed_opportunity_ids})

    # Add user context as evidence
    if body.additional_context:
        from core.schemas import EvidenceSource
        import uuid
        ev = EvidenceItem(
            evidence_id=str(uuid.uuid4()), run_id=run_id,
            source_type=EvidenceSource.USER_PROVIDED, source_ref="user_refinement",
            title="User-provided context during refinement",
            snippet=body.additional_context, relevance_score=0.9,
        )
        run_manager.add_evidence(run_id, ev)

    # Re-compose report with updated state
    run = run_manager.get_run(run_id)
    state = run.reasoning_state or ReasoningState()
    intake = run.company_intake
    budget_state = run.budget_state or BudgetState()
    evidence = get_evidence_store().get_all(run_id)

    from engines.pitch.composer import compose_report as _compose
    report = _compose(intake, run.opportunities, evidence, state, budget_state, assumptions=run.assumptions)
    report["metadata"]["refinement_count"] = report["metadata"].get("refinement_count", 0) + 1
    run_manager.store_report(run_id, report)

    emit(run_id, EventType.REPORT_REFINED, {"changes": changes})
    return {"report": report, "changes": changes}


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
