"""Tests for api/routes/pitch.py -- synthesis, publish, evidence, and report endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import app
from core import run_manager
from core.schemas import EvidenceItem, EvidenceSource, ReasoningState
from services.storage.memory_store import MemoryStore

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_state():
    run_manager.init_storage(MemoryStore())
    from services.memory.opp_store import get_opportunity_store
    from services.memory.report_store import get_report_store
    from services.memory.store import get_evidence_store

    get_evidence_store()._items.clear()
    get_opportunity_store()._items.clear()
    get_report_store()._items.clear()
    yield
    run_manager.init_storage(MemoryStore())
    get_evidence_store()._items.clear()
    get_opportunity_store()._items.clear()
    get_report_store()._items.clear()


def _run_id() -> str:
    """Create a run in legacy mode so assumptions/reasoning/synthesis flow works."""
    run = run_manager.create_run(
        "Acme Corp",
        "logistics",
        config_overrides={"orchestration.mode": "legacy"},
    )
    return run.run_id


def _create_reasoning_complete_run(rid: str) -> None:
    client.put(f"/v1/runs/{rid}/company-intake", json={"company_name": "Acme Corp", "industry": "logistics"})
    client.post(f"/v1/runs/{rid}/start")
    client.post(f"/v1/runs/{rid}/assumptions/confirm")
    client.post(f"/v1/runs/{rid}/start")
    run = run_manager.get_run(rid)
    assert run is not None
    state = ReasoningState(
        current_loop=3,
        completed=True,
        stop_reason="depth_budget_exhausted",
        overall_confidence=0.6,
        loops_completed=3,
    )
    run_manager.update_reasoning_state(rid, state)
    ev = EvidenceItem(
        evidence_id="ev-test-001",
        run_id=rid,
        source_type=EvidenceSource.WINS_KB,
        source_ref="eng-001",
        title="Support team ticket routing",
        snippet="customer support triage chatbot routing help desk deflection",
        relevance_score=0.85,
    )
    run_manager.add_evidence(rid, [ev])


def test_synthesize_from_reasoning():
    rid = _run_id()
    _create_reasoning_complete_run(rid)
    r = client.post(f"/v1/runs/{rid}/synthesize")
    assert r.status_code == 200
    d = r.json()
    assert "opportunities" in d
    assert "tier_counts" in d
    assert isinstance(d["opportunities"], list)


def test_synthesize_wrong_status():
    rid = _run_id()
    client.put(f"/v1/runs/{rid}/company-intake", json={"company_name": "Acme Corp", "industry": "logistics"})
    r = client.post(f"/v1/runs/{rid}/synthesize")
    assert r.status_code == 409


def test_synthesize_incomplete_reasoning():
    rid = _run_id()
    client.put(f"/v1/runs/{rid}/company-intake", json={"company_name": "Acme Corp", "industry": "logistics"})
    client.post(f"/v1/runs/{rid}/start")
    client.post(f"/v1/runs/{rid}/assumptions/confirm")
    client.post(f"/v1/runs/{rid}/start")
    r = client.post(f"/v1/runs/{rid}/synthesize")
    run = run_manager.get_run(rid)
    if run and run.reasoning_state and not run.reasoning_state.completed:
        assert r.status_code == 400


def test_publish_from_report():
    rid = _run_id()
    _create_reasoning_complete_run(rid)
    client.post(f"/v1/runs/{rid}/synthesize")
    r = client.post(f"/v1/runs/{rid}/publish")
    assert r.status_code == 200
    assert r.json()["status"] == "published"


def test_publish_wrong_status():
    rid = _run_id()
    client.put(f"/v1/runs/{rid}/company-intake", json={"company_name": "Acme Corp", "industry": "logistics"})
    r = client.post(f"/v1/runs/{rid}/publish")
    assert r.status_code == 409


def test_get_evidence():
    rid = _run_id()
    _create_reasoning_complete_run(rid)
    r = client.get(f"/v1/runs/{rid}/evidence")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_report():
    rid = _run_id()
    _create_reasoning_complete_run(rid)
    client.post(f"/v1/runs/{rid}/synthesize")
    r = client.get(f"/v1/runs/{rid}/report")
    assert r.status_code == 200
    body = r.json()
    assert "operator_brief" in body


def test_get_opportunities():
    rid = _run_id()
    _create_reasoning_complete_run(rid)
    client.post(f"/v1/runs/{rid}/synthesize")
    r = client.get(f"/v1/runs/{rid}/opportunities")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
