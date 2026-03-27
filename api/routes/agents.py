"""Agent state, hypothesis, and interaction endpoints for multi-agent runs."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import run_manager
from core.schemas import (
    AgentState,
    Hypothesis,
    ReportRefineRequest,
    Run,
    RunStatus,
    UserInteractionPoint,
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
        interactions=interactions, pending=pending, resolved=resolved,
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
        run_id=run_id, status="hypothesis_testing",
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

    # Handle "deepen" — backtrack to hypothesis testing
    if deepens:
        run_manager.transition(run_id, RunStatus.HYPOTHESIS_TESTING)
        return run_manager.get_run(run_id)

    # Handle "edit" — regenerate report in-place, stay at REVIEW
    if edits:
        from engines.orchestrator_helpers import generate_report
        from engines.hypothesis_tracker import HypothesisTracker

        tracker = HypothesisTracker()
        for h in run.hypotheses:
            tracker._hypotheses[h.hypothesis_id] = h

        result = await generate_report(
            run_id, run, tracker,
            run.config_snapshot,
            _get_grounder(run.config_snapshot),
            None,  # rag not needed for edit-only re-synthesis
            feedback=edits,
        )
        if result and result.adaptive_report:
            run_manager.store_adaptive_report(run_id, result.adaptive_report)

    return run_manager.get_run(run_id)


def _get_grounder(config: dict) -> object:
    """Obtain a grounder instance for report re-synthesis."""
    from api.routes.grounding import _build_client
    from services.grounder.grounder import Grounder
    client = _build_client(config)
    return Grounder(client=client, config=config)
