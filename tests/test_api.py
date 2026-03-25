"""Tests for api/app.py — endpoint integration using FastAPI TestClient."""
import pytest
from fastapi.testclient import TestClient

from api.app import app
from core import run_manager

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_run_store():
    """Isolate in-memory state between tests."""
    run_manager._runs.clear()
    from services.memory.store import get_evidence_store
    get_evidence_store()._items.clear()
    yield
    run_manager._runs.clear()
    get_evidence_store()._items.clear()


def _create_run(company_name: str = "Acme Corp", industry: str = "logistics") -> dict:
    resp = client.post("/v1/runs", json={"company_name": company_name, "industry": industry})
    assert resp.status_code == 201
    return resp.json()


# --- Health ---

def test_health_returns_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# --- POST /v1/runs ---

def test_create_run_returns_201():
    resp = client.post("/v1/runs", json={"company_name": "Acme", "industry": "logistics"})
    assert resp.status_code == 201


def test_create_run_returns_run_id():
    data = _create_run()
    assert "run_id" in data
    assert data["run_id"] is not None


def test_create_run_status_is_created():
    data = _create_run()
    assert data["status"] == "created"


def test_create_run_has_budgets():
    data = _create_run()
    assert "budgets" in data
    assert data["budgets"]["rag_query_budget"] == 8


def test_create_run_has_config_snapshot():
    data = _create_run()
    assert "config_snapshot" in data
    assert isinstance(data["config_snapshot"], dict)


# --- GET /v1/runs/{id} ---

def test_get_run_returns_run():
    created = _create_run()
    run_id = created["run_id"]
    resp = client.get(f"/v1/runs/{run_id}")
    assert resp.status_code == 200
    assert resp.json()["run_id"] == run_id


def test_get_run_nonexistent_returns_404():
    resp = client.get("/v1/runs/nonexistent-id-xyz")
    assert resp.status_code == 404


# --- PUT /v1/runs/{id}/company-intake ---

def test_update_intake_returns_intake_status():
    created = _create_run()
    run_id = created["run_id"]
    resp = client.put(
        f"/v1/runs/{run_id}/company-intake",
        json={"company_name": "Acme Corp", "industry": "logistics"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "intake"


def test_update_intake_stores_company_data():
    created = _create_run()
    run_id = created["run_id"]
    resp = client.put(
        f"/v1/runs/{run_id}/company-intake",
        json={
            "company_name": "Acme Corp",
            "industry": "logistics",
            "employee_count_band": "100-500",
        },
    )
    assert resp.status_code == 200
    intake = resp.json()["company_intake"]
    assert intake["company_name"] == "Acme Corp"
    assert intake["employee_count_band"] == "100-500"


# --- GET /v1/runs/{id}/ui ---

def test_get_ui_returns_ui_hints():
    created = _create_run()
    run_id = created["run_id"]
    resp = client.get(f"/v1/runs/{run_id}/ui")
    assert resp.status_code == 200
    data = resp.json()
    assert "stage_title" in data


def test_get_ui_created_status_shows_intake_title():
    created = _create_run()
    run_id = created["run_id"]
    resp = client.get(f"/v1/runs/{run_id}/ui")
    assert resp.json()["stage_title"] == "Company Intake"


def test_get_ui_intake_status_shows_different_title():
    created = _create_run()
    run_id = created["run_id"]
    client.put(
        f"/v1/runs/{run_id}/company-intake",
        json={"company_name": "Acme", "industry": "logistics"},
    )
    resp = client.get(f"/v1/runs/{run_id}/ui")
    assert resp.json()["stage_title"] == "Generating Assumptions"


def test_get_ui_nonexistent_returns_404():
    resp = client.get("/v1/runs/no-such-run/ui")
    assert resp.status_code == 404


# --- GET /v1/runs/{id}/trace ---

def test_get_trace_returns_list():
    created = _create_run()
    run_id = created["run_id"]
    resp = client.get(f"/v1/runs/{run_id}/trace")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_trace_has_run_created_event():
    created = _create_run()
    run_id = created["run_id"]
    resp = client.get(f"/v1/runs/{run_id}/trace")
    event_types = [e["event_type"] for e in resp.json()]
    assert "RUN_CREATED" in event_types
