"""Agent state, hypothesis, and interaction endpoints for multi-agent runs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import run_manager
from core.schemas import (
    AgentState,
    Hypothesis,
    HypothesisStatus,
    Run,
    RunStatus,
    UserInteractionPoint,
)
from api.schemas import (
    EnrichRequest,
    EnrichResponse,
    HypothesisDelta,
    ReportRefineRequest,
)

router = APIRouter()


# --- Response models ---


class AgentListResponse(BaseModel):
    agents: list[AgentState]
    count: int


class HypothesisListResponse(BaseModel):
    hypotheses: list[Hypothesis]
    count: int


class InteractionListResponse(BaseModel):
    interactions: list[UserInteractionPoint]
    pending: int
    resolved: int


class InteractionResponse(BaseModel):
    interaction_id: str
    response: str


class ReviewResponse(BaseModel):
    run_id: str
    status: str
    message: str


# --- Helpers ---


def _get_run_or_404(run_id: str):
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return run


# --- Endpoints ---


@router.get("/runs/{run_id}/agents", response_model=AgentListResponse)
def list_agents(run_id: str) -> AgentListResponse:
    run = _get_run_or_404(run_id)
    return AgentListResponse(agents=run.agent_states, count=len(run.agent_states))


@router.get("/runs/{run_id}/hypotheses", response_model=HypothesisListResponse)
def list_hypotheses(run_id: str) -> HypothesisListResponse:
    run = _get_run_or_404(run_id)
    return HypothesisListResponse(hypotheses=run.hypotheses, count=len(run.hypotheses))


@router.get("/runs/{run_id}/hypotheses/{hid}", response_model=Hypothesis)
def get_hypothesis(run_id: str, hid: str) -> Hypothesis:
    run = _get_run_or_404(run_id)
    for h in run.hypotheses:
        if h.hypothesis_id == hid:
            return h
    raise HTTPException(status_code=404, detail=f"Hypothesis not found: {hid}")


@router.get("/runs/{run_id}/interactions", response_model=InteractionListResponse)
def list_interactions(run_id: str) -> InteractionListResponse:
    run = _get_run_or_404(run_id)
    interactions = run.user_interactions
    pending = sum(1 for i in interactions if i.response is None and i.requires_response)
    resolved = sum(1 for i in interactions if i.response is not None)
    return InteractionListResponse(
        interactions=interactions,
        pending=pending,
        resolved=resolved,
    )


@router.post("/runs/{run_id}/interactions/{iid}/respond", response_model=UserInteractionPoint)
def respond_to_interaction(run_id: str, iid: str, body: InteractionResponse) -> UserInteractionPoint:
    run = _get_run_or_404(run_id)
    for interaction in run.user_interactions:
        if interaction.interaction_id == iid:
            if interaction.response is not None:
                raise HTTPException(status_code=422, detail="Interaction already resolved")
            interaction.response = body.response
            return interaction
    raise HTTPException(status_code=404, detail=f"Interaction not found: {iid}")


@router.post("/runs/{run_id}/review/approve", response_model=ReviewResponse)
def approve_review(run_id: str) -> ReviewResponse:
    run = _get_run_or_404(run_id)
    if run.status != RunStatus.REVIEW:
        raise HTTPException(
            status_code=422,
            detail=f"Run must be in REVIEW status, got: {run.status.value}",
        )
    run_manager.transition(run_id, RunStatus.PUBLISHED)
    return ReviewResponse(run_id=run_id, status="published", message="Report approved and published")


@router.post("/runs/{run_id}/review/investigate", response_model=ReviewResponse)
def request_investigation(run_id: str) -> ReviewResponse:
    run = _get_run_or_404(run_id)
    if run.status != RunStatus.REVIEW:
        raise HTTPException(
            status_code=422,
            detail=f"Run must be in REVIEW status, got: {run.status.value}",
        )
    run_manager.transition(run_id, RunStatus.HYPOTHESIS_TESTING)
    return ReviewResponse(
        run_id=run_id,
        status="hypothesis_testing",
        message="Returning to hypothesis testing for deeper investigation",
    )


@router.post("/runs/{run_id}/report/refine", response_model=Run)
async def refine_report(run_id: str, body: ReportRefineRequest) -> Run:
    """Refine the report based on user feedback.

    - "edit" feedback: re-runs ReportSynthesizer with feedback,
      stays at REVIEW.
    - "deepen": transitions to HYPOTHESIS_TESTING for re-test.
    - "reinvestigate": transitions to DEEP_RESEARCH for full re-run.
    """
    run = _get_run_or_404(run_id)
    if run.status != RunStatus.REVIEW:
        raise HTTPException(
            status_code=422,
            detail=f"Run must be in REVIEW status, got: {run.status.value}",
        )

    edits = [f for f in body.feedbacks if f.feedback_type == "edit"]
    deepens = [f for f in body.feedbacks if f.feedback_type == "deepen"]
    reinvestigates = [f for f in body.feedbacks if f.feedback_type == "reinvestigate"]

    # Store all feedback on run history
    run.feedback_history.extend(body.feedbacks)

    # Handle "reinvestigate" — backtrack furthest
    if reinvestigates:
        run_manager.transition(run_id, RunStatus.DEEP_RESEARCH)
        return run_manager.get_run(run_id)

    # Handle "deepen" — targeted re-test of specific hypotheses, then re-generate report
    if deepens:
        from engines.hypothesis_tracker import HypothesisTracker
        from engines.orchestrator_helpers import generate_report, test_hypotheses

        tracker = HypothesisTracker()
        for h in run.hypotheses:
            tracker._hypotheses[h.hypothesis_id] = h

        grounder = _get_grounder(run.config_snapshot)
        rag = _get_rag()

        # Find only the targeted hypotheses
        target_ids = set()
        for fb in deepens:
            # target_section is "opportunity:{hyp_id}"
            if ":" in fb.target_section:
                target_ids.add(fb.target_section.split(":", 1)[1])
        targets = [h for h in run.hypotheses if h.hypothesis_id in target_ids]
        if not targets:
            targets = run.hypotheses  # fallback: re-test all if no match

        # Re-test only the targeted hypotheses
        await test_hypotheses(
            run_id,
            targets,
            run.budget_state,
            tracker,
            run.config_snapshot,
            grounder,
            rag,
        )

        # Sync updated hypotheses back to run
        for h in run.hypotheses:
            updated = tracker.get(h.hypothesis_id)
            if updated:
                h.status = updated.status
                h.confidence = updated.confidence
                h.test_results = updated.test_results
                h.reasoning_chain = updated.reasoning_chain
                h.conditions_for_success = updated.conditions_for_success

        # Re-generate report with deepen feedback context
        result = await generate_report(
            run_id,
            run,
            tracker,
            run.config_snapshot,
            grounder,
            rag,
            feedback=deepens,
        )
        if result and result.adaptive_report:
            run_manager.store_adaptive_report(run_id, result.adaptive_report)

        return run_manager.get_run(run_id)

    # Handle "edit" — regenerate report in-place, stay at REVIEW
    if edits:
        from engines.hypothesis_tracker import HypothesisTracker
        from engines.orchestrator_helpers import generate_report

        tracker = HypothesisTracker()
        for h in run.hypotheses:
            tracker._hypotheses[h.hypothesis_id] = h

        result = await generate_report(
            run_id,
            run,
            tracker,
            run.config_snapshot,
            _get_grounder(run.config_snapshot),
            None,  # rag not needed for edit-only re-synthesis
            feedback=edits,
        )
        if result and result.adaptive_report:
            run_manager.store_adaptive_report(run_id, result.adaptive_report)

    return run_manager.get_run(run_id)


@router.post("/runs/{run_id}/enrich", response_model=EnrichResponse)
async def enrich_run(run_id: str, body: EnrichRequest) -> EnrichResponse:
    """Inject analyst-provided evidence, re-test affected hypotheses, regenerate report."""
    from core.events import EventType
    from engines.enrichment import prepare_enrichment
    from engines.hypothesis_tracker import HypothesisTracker
    from engines.orchestrator_helpers import generate_report, test_hypotheses
    from services.trace import emit

    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if run.status not in (RunStatus.REVIEW, RunStatus.PUBLISHED):
        raise HTTPException(status_code=409, detail=f"Cannot enrich from status: {run.status.value}")

    emit(run_id, EventType.ENRICHMENT_SUBMITTED, {"input_count": len(body.inputs)})

    enrichment = prepare_enrichment(run, body.inputs)
    run_manager.add_evidence(run_id, enrichment.evidence_items, source_label="enrichment", phase="enrichment")

    # Re-test affected hypotheses
    tracker = HypothesisTracker()
    for h in run.hypotheses:
        tracker._hypotheses[h.hypothesis_id] = h
    targets = [h for h in run.hypotheses if h.hypothesis_id in enrichment.affected_hypothesis_ids]

    if targets:
        config = run.config_snapshot
        grounder = _get_grounder(config)
        rag = _get_rag(config)
        await test_hypotheses(run_id, targets, run.budget_state, tracker, config, grounder, rag)

        # Force-finalize and sync back
        validate_thresh = float(config.get("reasoning", {}).get("confidence_threshold", 0.7))
        reject_thresh = validate_thresh * 0.3
        for h in tracker.get_all():
            if h.status == HypothesisStatus.TESTING:
                if h.confidence >= validate_thresh:
                    tracker.validate(h.hypothesis_id, f"Enrichment: confidence {h.confidence:.0%}")
                elif h.confidence < reject_thresh:
                    tracker.reject(h.hypothesis_id, f"Enrichment: confidence {h.confidence:.0%}")
        run_manager.add_hypotheses(run_id, tracker.get_all())

        # Regenerate report
        run = run_manager.get_run(run_id)
        assert run is not None
        result = await generate_report(run_id, run, tracker, config, grounder, rag)
        if result and result.adaptive_report:
            run_manager.store_adaptive_report(run_id, result.adaptive_report)

    # Build deltas
    run = run_manager.get_run(run_id)
    assert run is not None
    deltas = []
    for hid, old_conf in enrichment.pre_enrichment_confidence.items():
        h = next((h for h in run.hypotheses if h.hypothesis_id == hid), None)
        if h:
            deltas.append(
                HypothesisDelta(
                    hypothesis_id=hid,
                    statement=h.statement[:80],
                    confidence_before=old_conf,
                    confidence_after=h.confidence,
                    status_before=enrichment.pre_enrichment_status.get(hid, "unknown"),
                    status_after=h.status.value if hasattr(h.status, "value") else str(h.status),
                )
            )

    emit(
        run_id,
        EventType.ENRICHMENT_COMPLETED,
        {"evidence_added": len(enrichment.evidence_items), "deltas": len(deltas)},
    )

    return EnrichResponse(
        run_id=run_id,
        evidence_added=len(enrichment.evidence_items),
        hypotheses_affected=len(enrichment.affected_hypothesis_ids),
        deltas=deltas,
        message=f"Enrichment complete: {len(deltas)} hypotheses re-evaluated",
    )


def _get_grounder(config: dict) -> object:
    """Obtain a grounder instance for report re-synthesis."""
    from api.client_factory import build_gemini_client
    from services.grounder.grounder import Grounder

    client = build_gemini_client(config)
    return Grounder(client=client, config=config)


def _get_rag(config: dict) -> object:
    """Obtain RAG retriever for re-testing."""
    from services.rag.ingest import ensure_loaded
    from services.rag.retrieval import RAGRetriever
    from services.rag.store import get_rag_store

    store = get_rag_store()
    ensure_loaded(store)
    return RAGRetriever(store=store, config=config)


def _get_rag() -> object:
    """Obtain a RAG retriever for targeted hypothesis re-testing."""
    from services.rag.ingest import ensure_loaded
    from services.rag.retrieval import RAGRetriever
    from services.rag.store import get_rag_store

    store = get_rag_store()
    ensure_loaded(store)
    return RAGRetriever(store=store, config={})
