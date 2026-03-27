from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException

from core import run_manager
from core.events import EventType
from core.schemas import (
    AssumptionsDraft,
    EvidenceItem,
    EvidenceSource,
    Provenance,
    ReasoningLoopResult,
    ReasoningState,
    Run,
    RunStatus,
    UserAnswer,
)
from engines.thought import ThoughtEngine
from services.grounder.grounder import Grounder
from services.rag.ingest import ensure_loaded
from services.rag.retrieval import RAGRetriever
from services.rag.store import get_rag_store
from services.memory.router import ContextRouter
from services.memory.store import get_evidence_store
from services.trace import emit

_ctx_router = ContextRouter()

router = APIRouter()


def _load_engagements() -> dict[str, dict]:
    import json
    path = Path(__file__).parent.parent.parent / "data" / "wins_kb_seed" / "engagements.json"
    with open(path) as f:
        return {r["engagement_id"]: r for r in json.load(f)}


def _make_engine(config: dict) -> ThoughtEngine:
    from api.routes.grounding import _build_client
    client = _build_client(config)
    grounder = Grounder(client=client, config=config)
    store = get_rag_store()
    ensure_loaded(store)
    retriever = RAGRetriever(store=store, config=config)
    return ThoughtEngine(
        grounder=grounder, rag_retriever=retriever, config=config,
        engagement_lookup=_load_engagements(),
    )


@router.post("/runs/{run_id}/start")
async def start_run(run_id: str) -> AssumptionsDraft | ReasoningLoopResult:
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    # Multi-agent mode: skip assumptions, go straight to orchestrator
    mode = run.config_snapshot.get("orchestration", {}).get("mode", "legacy")
    if mode == "multi_agent" and run.status == RunStatus.INTAKE:
        if run.company_intake is None:
            raise HTTPException(status_code=400, detail="Company intake missing")
        return await _start_multi_agent(run_id, run)

    # Legacy mode: INTAKE → generate assumptions
    if run.status == RunStatus.INTAKE:
        if run.company_intake is None:
            raise HTTPException(status_code=400, detail="Company intake not submitted")
        engine = _make_engine(run.config_snapshot)
        draft = engine.generate_assumptions(run_id, run.company_intake, run.budget_state)
        run_manager.transition(run_id, RunStatus.ASSUMPTIONS_DRAFT)
        run_manager.update_assumptions(run_id, draft)
        return draft

    # Legacy mode: ASSUMPTIONS_CONFIRMED → start reasoning
    if run.status == RunStatus.ASSUMPTIONS_CONFIRMED:
        if run.company_intake is None:
            raise HTTPException(status_code=400, detail="Company intake missing")
        return _start_legacy(run_id, run)

    raise HTTPException(status_code=409, detail=f"Cannot start from status: {run.status.value}")


def _start_legacy(run_id: str, run: Run) -> ReasoningLoopResult:
    assumptions = run.assumptions or AssumptionsDraft(assumptions=[], open_questions=[])
    engine = _make_engine(run.config_snapshot)
    run_manager.transition(run_id, RunStatus.REASONING)
    result = engine.run_loop(run_id, run.company_intake, assumptions, run.budget_state)
    eids = [e.evidence_id for e in result.evidence_items] if result.evidence_items else []
    state = ReasoningState(
        current_loop=result.loops_run, evidence_ids=eids,
        field_coverage=result.field_coverage, overall_confidence=result.overall_confidence,
        pending_question=result.pending_question, completed=result.completed,
        stop_reason=result.stop_reason, coverage_gaps=result.coverage_gaps,
        loops_completed=result.loops_run, escalation_reason=result.escalation_reason,
        escalation_fields=result.escalation_fields, contradictions=result.contradictions,
        confidence_history=result.confidence_history,
    )
    run_manager.add_evidence(run_id, result.evidence_items, source_label="reasoning_loop")
    run_manager.update_reasoning_state(run_id, state)
    return result


async def _start_multi_agent(run_id: str, run: Run) -> Run:
    """Launch the multi-agent orchestrator pipeline."""
    from engines.orchestrator import Orchestrator
    from api.routes.grounding import _build_client
    config = run.config_snapshot
    grounder = Grounder(client=_build_client(config), config=config)
    store = get_rag_store()
    ensure_loaded(store)
    orch = Orchestrator(
        config=config, grounder=grounder,
        rag_retriever=RAGRetriever(store=store, config=config),
    )
    return await orch.run(run_id)


@router.post("/runs/{run_id}/assumptions/confirm", response_model=Run)
def confirm_assumptions(run_id: str, body: AssumptionsDraft | None = None) -> Run:
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if run.status != RunStatus.ASSUMPTIONS_DRAFT:
        raise HTTPException(status_code=409, detail=f"Cannot confirm from status: {run.status.value}")
    confirmed = body if body is not None else run.assumptions
    if confirmed is None:
        confirmed = AssumptionsDraft(assumptions=[], open_questions=[])
    run_manager.update_assumptions(run_id, confirmed)
    run_manager.transition(run_id, RunStatus.ASSUMPTIONS_CONFIRMED)
    edits = body is not None
    emit(run_id, EventType.ASSUMPTIONS_CONFIRMED, {
        "fields_count": len(confirmed.assumptions),
        "edits_made": edits,
    })
    return run_manager.get_run(run_id)  # type: ignore[return-value]


@router.post("/runs/{run_id}/answer", response_model=ReasoningLoopResult)
def answer_question(run_id: str, body: UserAnswer) -> ReasoningLoopResult:
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if run.status != RunStatus.REASONING:
        raise HTTPException(status_code=409, detail=f"Run not in REASONING status: {run.status.value}")
    state = run.reasoning_state
    if state is None or state.pending_question is None:
        raise HTTPException(status_code=400, detail="No pending question to answer")
    if state.pending_question.question_id != body.question_id:
        raise HTTPException(status_code=400, detail="question_id does not match pending question")
    emit(run_id, EventType.USER_ANSWER_RECEIVED, {
        "question_id": body.question_id,
        "answer_length": len(body.answer_text),
    })
    answer_evidence = EvidenceItem(
        evidence_id=str(uuid.uuid4()),
        run_id=run_id,
        source_type=EvidenceSource.USER_PROVIDED,
        source_ref=body.question_id,
        title=state.pending_question.field,
        snippet=body.answer_text,
        relevance_score=1.0,
        confidence_score=1.0,
        retrieval_meta={"question_id": body.question_id, "field": state.pending_question.field},
        provenance=Provenance(
            source_type="raw",
            source_evidence_ids=[body.question_id],
            confidence=1.0,
        ),
    )
    run_manager.add_evidence(run_id, [answer_evidence], source_label="user_answer")
    if run.company_intake is None:
        raise HTTPException(status_code=400, detail="Company intake missing")
    assumptions = run.assumptions or AssumptionsDraft(assumptions=[], open_questions=[])
    engine = _make_engine(run.config_snapshot)
    # Route context: filter existing evidence before passing to loop
    thought_ctx = _ctx_router.recall_for_thought(
        run_id, get_evidence_store().get_all(run_id), run.company_intake,
        run.budget_state, run.config_snapshot,
        unresolved_fields=state.coverage_gaps if state else None,
    )
    result = engine.run_loop(
        run_id,
        run.company_intake,
        assumptions,
        run.budget_state,
        existing_evidence=thought_ctx.relevant_evidence,
        start_loop=state.loops_completed,
    )
    new_state = ReasoningState(
        current_loop=result.loops_run,
        evidence_ids=[e.evidence_id for e in result.evidence_items],
        field_coverage=result.field_coverage, overall_confidence=result.overall_confidence,
        pending_question=result.pending_question, completed=result.completed,
        stop_reason=result.stop_reason, coverage_gaps=result.coverage_gaps,
        loops_completed=result.loops_run, escalation_reason=result.escalation_reason,
        escalation_fields=result.escalation_fields, contradictions=result.contradictions,
        confidence_history=result.confidence_history,
    )
    run_manager.add_evidence(run_id, result.evidence_items, source_label="reasoning_loop_resumed")
    run_manager.update_reasoning_state(run_id, new_state)
    return result
