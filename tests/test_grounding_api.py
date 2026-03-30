"""Tests for api/routes/grounding.py — POST /v1/runs/{id}/ground endpoint."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.app import app
from core import run_manager
from core.schemas import EvidenceSource
from services.grounder.fake_client import FakeGeminiClient
from services.storage.memory_store import MemoryStore

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_run_store():
    run_manager.init_storage(MemoryStore())
    yield
    run_manager.init_storage(MemoryStore())


def _create_run() -> dict:
    resp = client.post("/v1/runs", json={"company_name": "Acme", "industry": "logistics"})
    assert resp.status_code == 201
    return resp.json()


def _fake_patch():
    """Patch _build_client to always return a FakeGeminiClient."""
    return patch("api.routes.grounding._build_client", return_value=FakeGeminiClient())


def test_ground_returns_200():
    run_data = _create_run()
    with _fake_patch():
        resp = client.post(f"/v1/runs/{run_data['run_id']}/ground", json={"prompt": "What does Acme do?"})
    assert resp.status_code == 200


def test_ground_unknown_run_returns_404():
    resp = client.post("/v1/runs/no-such-run/ground", json={"prompt": "What does Acme do?"})
    assert resp.status_code == 404


def test_ground_response_has_evidence_items():
    run_data = _create_run()
    with _fake_patch():
        resp = client.post(f"/v1/runs/{run_data['run_id']}/ground", json={"prompt": "What does Acme do?"})
    data = resp.json()
    assert "evidence_items" in data
    assert isinstance(data["evidence_items"], list)


def test_ground_evidence_items_have_google_search_source():
    run_data = _create_run()
    with _fake_patch():
        resp = client.post(f"/v1/runs/{run_data['run_id']}/ground", json={"prompt": "What does Acme do?"})
    data = resp.json()
    for item in data["evidence_items"]:
        assert item["source_type"] == EvidenceSource.GOOGLE_SEARCH.value


def test_ground_budget_state_updated_on_run():
    run_data = _create_run()
    run_id = run_data["run_id"]
    with _fake_patch():
        client.post(f"/v1/runs/{run_id}/ground", json={"prompt": "What does Acme do?"})
    run = run_manager.get_run(run_id)
    assert run.budget_state.external_search_calls_used == 1
    assert run.budget_state.external_search_queries_used > 0


def test_ground_budget_exhaustion_returns_budget_exhausted_true():
    run_data = _create_run()
    run_id = run_data["run_id"]
    run = run_manager.get_run(run_id)
    run.budget_state.external_search_queries_used = 25  # saturate budget (matches defaults.yaml)

    with _fake_patch():
        resp = client.post(f"/v1/runs/{run_id}/ground", json={"prompt": "What does Acme do?"})
    assert resp.json()["budget_exhausted"] is True


def test_ground_multiple_calls_decrement_budget():
    run_data = _create_run()
    run_id = run_data["run_id"]
    with _fake_patch():
        client.post(f"/v1/runs/{run_id}/ground", json={"prompt": "Query 1"})
        client.post(f"/v1/runs/{run_id}/ground", json={"prompt": "Query 2"})
    run = run_manager.get_run(run_id)
    assert run.budget_state.external_search_calls_used == 2


def test_ground_response_has_search_queries_used():
    run_data = _create_run()
    with _fake_patch():
        resp = client.post(f"/v1/runs/{run_data['run_id']}/ground", json={"prompt": "What does Acme do?"})
    data = resp.json()
    assert "search_queries_used" in data
    assert data["search_queries_used"] >= 0


def test_ground_evidence_items_are_valid_schema():
    run_data = _create_run()
    with _fake_patch():
        resp = client.post(f"/v1/runs/{run_data['run_id']}/ground", json={"prompt": "What does Acme do?"})
    data = resp.json()
    required_fields = {"evidence_id", "run_id", "source_type", "source_ref", "title", "snippet"}
    for item in data["evidence_items"]:
        for field in required_fields:
            assert field in item, f"Missing field: {field}"
