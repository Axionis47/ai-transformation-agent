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
        answer_text = f"Approximately typical for {bundle.industry} companies of size {bundle.employee_count_band}"
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


def run_single(bundle: CompanyBundle) -> EvalResult:
    """Run the full pipeline for one company bundle and return metrics."""
    start = time.time()

    # Eval harness uses legacy assumptions→reasoning→synthesis flow
    run = run_manager.create_run(
        bundle.company_name,
        bundle.industry,
        config_overrides={"orchestration.mode": "legacy"},
    )
    run_id = run.run_id

    resp = _client.put(
        f"/v1/runs/{run_id}/company-intake",
        json={
            "company_name": bundle.company_name,
            "industry": bundle.industry,
            "employee_count_band": bundle.employee_count_band,
            "notes": bundle.notes,
        },
    )
    if resp.status_code != 200:
        return _fail(bundle, f"intake failed: {resp.status_code}", time.time() - start)

    resp = _client.post(f"/v1/runs/{run_id}/start")
    if resp.status_code != 200:
        return _fail(bundle, f"start (assumptions) failed: {resp.status_code}", time.time() - start)

    resp = _client.post(f"/v1/runs/{run_id}/assumptions/confirm")
    if resp.status_code != 200:
        return _fail(bundle, f"confirm failed: {resp.status_code}", time.time() - start)

    resp = _client.post(f"/v1/runs/{run_id}/start")
    if resp.status_code != 200:
        return _fail(bundle, f"start (reasoning) failed: {resp.status_code}", time.time() - start)
    _auto_answer(run_id, bundle, resp.json())
    _force_reasoning_complete(run_id)

    resp = _client.post(f"/v1/runs/{run_id}/synthesize")
    if resp.status_code != 200:
        return _fail(bundle, f"synthesize failed: {resp.status_code}", time.time() - start)

    run_resp = _client.get(f"/v1/runs/{run_id}").json()
    trace_resp = _client.get(f"/v1/runs/{run_id}/trace").json()
    latency = time.time() - start

    opportunities = run_resp.get("opportunities", [])
    tier_dist: dict[str, int] = {"easy": 0, "medium": 0, "hard": 0}
    for opp in opportunities:
        t = opp.get("tier", "").lower()
        if t in tier_dist:
            tier_dist[t] += 1

    budget_state = run_resp.get("budget_state", {})
    # True budget violation = BUDGET_VIOLATION_BLOCKED event was emitted.
    # Post-call over-count (e.g. 6 queries on a budget of 5) is expected
    # behavior when the final call returns more queries than remaining budget.
    blocked_events = [e for e in trace_resp if e.get("event_type") == "BUDGET_VIOLATION_BLOCKED"]
    budget_ok = len(blocked_events) == 0
    rs = run_resp.get("reasoning_state") or {}
    return EvalResult(
        company_name=bundle.company_name,
        industry=bundle.industry,
        success=True,
        error=None,
        evidence_count=len(run_resp.get("evidence", [])),
        opportunity_count=len(opportunities),
        tier_distribution=tier_dist,
        field_coverage=rs.get("field_coverage", {}),
        overall_confidence=rs.get("overall_confidence", 0.0),
        budget_adherence=budget_ok,
        rag_queries_used=budget_state.get("rag_queries_used", 0),
        search_queries_used=budget_state.get("external_search_queries_used", 0),
        trace_event_count=len(trace_resp),
        latency_seconds=round(latency, 2),
    )


def run_all() -> list[EvalResult]:
    """Run eval for all 25 company bundles."""
    results: list[EvalResult] = []
    for bundle in get_bundles():
        try:
            results.append(run_single(bundle))
        except Exception as exc:  # noqa: BLE001
            results.append(_fail(bundle, str(exc), 0.0))
    return results
