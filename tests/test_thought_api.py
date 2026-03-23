"""Tests for api/routes/thought.py -- thought engine API endpoints."""
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from api.app import app
from core import run_manager

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_state():
    run_manager._runs.clear()
    yield
    run_manager._runs.clear()


def _run_id() -> str:
    return client.post("/v1/runs", json={"company_name": "Acme Logistics", "industry": "logistics"}).json()["run_id"]


def _intake(rid: str):
    client.put(f"/v1/runs/{rid}/company-intake", json={"company_name": "Acme Logistics", "industry": "logistics"})


def _confirmed(rid: str):
    _intake(rid)
    client.post(f"/v1/runs/{rid}/start")
    client.post(f"/v1/runs/{rid}/assumptions/confirm")


def test_start_from_intake_returns_assumptions():
    rid = _run_id(); _intake(rid)
    r = client.post(f"/v1/runs/{rid}/start")
    assert r.status_code == 200
    d = r.json()
    assert "assumptions" in d or "open_questions" in d


def test_start_wrong_status_returns_409():
    assert client.post(f"/v1/runs/{_run_id()}/start").status_code == 409


def test_confirm_assumptions_transitions():
    rid = _run_id(); _intake(rid); client.post(f"/v1/runs/{rid}/start")
    r = client.post(f"/v1/runs/{rid}/assumptions/confirm")
    assert r.status_code == 200 and r.json()["status"] == "assumptions_confirmed"


def test_start_from_confirmed_returns_reasoning():
    rid = _run_id(); _confirmed(rid)
    r = client.post(f"/v1/runs/{rid}/start")
    assert r.status_code == 200
    d = r.json()
    assert "completed" in d and "evidence_items" in d


def test_answer_continues_reasoning():
    rid = _run_id(); _confirmed(rid)
    client.post(f"/v1/runs/{rid}/start")
    run = run_manager.get_run(rid)
    if run and run.reasoning_state and run.reasoning_state.pending_question:
        pq = run.reasoning_state.pending_question
        r = client.post(f"/v1/runs/{rid}/answer",
            json={"question_id": pq.question_id, "answer_text": "500 employees"})
        assert r.status_code == 200
