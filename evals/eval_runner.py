"""Eval runner: executes the full pipeline for each company bundle."""
from __future__ import annotations

import time
from dataclasses import dataclass

from fastapi.testclient import TestClient

from api.app import app
from core import run_manager
from evals.company_bundles import CompanyBundle, get_bundles

_client = TestClient(app)


@dataclass
class EvalResult:
    company_name: str
    industry: str
    success: bool
    error: str | None
    evidence_count: int
    opportunity_count: int
    tier_distribution: dict[str, int]
    field_coverage: dict[str, float]
    overall_confidence: float
    budget_adherence: bool
    rag_queries_used: int
    search_queries_used: int
    trace_event_count: int
    latency_seconds: float


def _fail(bundle: CompanyBundle, error: str, latency: float) -> EvalResult:
    return EvalResult(
        company_name=bundle.company_name,
        industry=bundle.industry,
        success=False,
        error=error,
        evidence_count=0,
        opportunity_count=0,
        tier_distribution={},
        field_coverage={},
        overall_confidence=0.0,
        budget_adherence=True,
        rag_queries_used=0,
        search_queries_used=0,
        trace_event_count=0,
        latency_seconds=round(latency, 2),
    )


def _auto_answer(run_id: str, bundle: CompanyBundle, result: dict, limit: int = 3) -> dict:
    """Answer pending questions up to `limit` times."""
    for _ in range(limit):
        pq = result.get("pending_question")
        if not pq:
            break
        answer_text = (
            f"Approximately typical for {bundle.industry} companies "
            f"of size {bundle.employee_count_band}"
        )
        resp = _client.post(
            f"/v1/runs/{run_id}/answer",
            json={"question_id": pq["question_id"], "answer_text": answer_text},
        )
        if resp.status_code != 200:
            break
        result = resp.json()
    return result


def _force_reasoning_complete(run_id: str) -> None:
    """Mark reasoning as completed so synthesize can proceed."""
    run = run_manager.get_run(run_id)
    if run and run.reasoning_state and not run.reasoning_state.completed:
        run.reasoning_state.completed = True
        run.reasoning_state.stop_reason = "eval_force_complete"
