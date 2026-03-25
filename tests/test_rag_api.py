"""Tests for api/routes/rag.py — POST /v1/runs/{id}/rag:query endpoint."""
import tempfile
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.app import app
from core import run_manager
from services.rag.ingest import ensure_loaded
from services.rag.store import RAGStore

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_run_store():
    """Isolate in-memory run state between tests."""
    run_manager._runs.clear()
    from services.memory.store import get_evidence_store
    get_evidence_store()._items.clear()
    yield
    run_manager._runs.clear()
    get_evidence_store()._items.clear()


@pytest.fixture
def tmpdir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def _make_seeded_store(persist_dir: str) -> RAGStore:
    store = RAGStore(persist_dir=persist_dir)
    ensure_loaded(store)
    return store


def _create_run() -> dict:
    resp = client.post("/v1/runs", json={"company_name": "Acme", "industry": "logistics"})
    assert resp.status_code == 201
    return resp.json()


# --- 200 success path ---

def test_rag_query_returns_200(tmpdir):
    run_data = _create_run()
    run_id = run_data["run_id"]
    with patch("api.routes.rag.RAGStore", return_value=_make_seeded_store(tmpdir)):
        resp = client.post(
            f"/v1/runs/{run_id}/rag:query",
            json={"query": "customer support automation"},
        )
    assert resp.status_code == 200


def test_rag_query_response_has_results_field(tmpdir):
    run_data = _create_run()
    run_id = run_data["run_id"]
    with patch("api.routes.rag.RAGStore", return_value=_make_seeded_store(tmpdir)):
        resp = client.post(
            f"/v1/runs/{run_id}/rag:query",
            json={"query": "customer support automation"},
        )
    data = resp.json()
    assert "results" in data


def test_rag_query_response_has_query_field(tmpdir):
    run_data = _create_run()
    run_id = run_data["run_id"]
    with patch("api.routes.rag.RAGStore", return_value=_make_seeded_store(tmpdir)):
        resp = client.post(
            f"/v1/runs/{run_id}/rag:query",
            json={"query": "fraud detection mid-market"},
        )
    data = resp.json()
    assert data["query"] == "fraud detection mid-market"


def test_rag_query_response_has_budget_exhausted_field(tmpdir):
    run_data = _create_run()
    run_id = run_data["run_id"]
    with patch("api.routes.rag.RAGStore", return_value=_make_seeded_store(tmpdir)):
        resp = client.post(
            f"/v1/runs/{run_id}/rag:query",
            json={"query": "logistics dispatch optimization"},
        )
    data = resp.json()
    assert "budget_exhausted" in data


def test_rag_query_first_call_not_budget_exhausted(tmpdir):
    run_data = _create_run()
    run_id = run_data["run_id"]
    store = _make_seeded_store(tmpdir)
    with patch("api.routes.rag.RAGStore", return_value=store):
        resp = client.post(
            f"/v1/runs/{run_id}/rag:query",
            json={"query": "customer support"},
        )
    assert resp.json()["budget_exhausted"] is False


# --- 404 for unknown run ---

def test_rag_query_nonexistent_run_returns_404():
    resp = client.post(
        "/v1/runs/nonexistent-run-xyz/rag:query",
        json={"query": "customer support"},
    )
    assert resp.status_code == 404


def test_rag_query_404_detail_mentions_run(tmpdir):
    resp = client.post(
        "/v1/runs/no-such-run/rag:query",
        json={"query": "fraud detection"},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# --- Budget exhaustion ---

def test_rag_query_budget_exhaustion_returns_budget_exhausted_true(tmpdir):
    """Call the endpoint more times than rag_query_budget allows."""
    run_data = _create_run()
    run_id = run_data["run_id"]
    budget = run_manager.get_run(run_id).budgets.rag_query_budget
    store = _make_seeded_store(tmpdir)

    last_resp = None
    with patch("api.routes.rag.RAGStore", return_value=store):
        for i in range(budget + 1):
            last_resp = client.post(
                f"/v1/runs/{run_id}/rag:query",
                json={"query": f"query number {i}"},
            )
    assert last_resp is not None
    assert last_resp.json()["budget_exhausted"] is True


def test_rag_query_budget_exhausted_results_empty(tmpdir):
    run_data = _create_run()
    run_id = run_data["run_id"]
    budget = run_manager.get_run(run_id).budgets.rag_query_budget
    store = _make_seeded_store(tmpdir)

    last_resp = None
    with patch("api.routes.rag.RAGStore", return_value=store):
        for i in range(budget + 1):
            last_resp = client.post(
                f"/v1/runs/{run_id}/rag:query",
                json={"query": f"query number {i}"},
            )
    assert last_resp is not None
    assert last_resp.json()["results"] == []
