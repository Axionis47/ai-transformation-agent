"""Tests for core/run_manager.py — run state machine."""
import pytest

from core import run_manager
from core.schemas import BudgetState, CompanyIntake, RunStatus


@pytest.fixture(autouse=True)
def clear_run_store():
    """Reset in-memory run store before each test to prevent cross-test pollution."""
    run_manager._runs.clear()
    from services.memory.store import get_evidence_store
    get_evidence_store()._items.clear()
    yield
    run_manager._runs.clear()
    get_evidence_store()._items.clear()


def test_create_run_returns_run():
    run = run_manager.create_run("Acme Corp", "logistics")
    assert run is not None
    assert run.run_id is not None


def test_create_run_status_is_created():
    run = run_manager.create_run("Acme Corp", "logistics")
    assert run.status == RunStatus.CREATED


def test_create_run_sets_config_snapshot():
    run = run_manager.create_run("Acme Corp", "logistics")
    assert isinstance(run.config_snapshot, dict)
    assert "budgets" in run.config_snapshot


def test_create_run_sets_budgets():
    run = run_manager.create_run("Acme Corp", "logistics")
    assert run.budgets.rag_query_budget == 8
    assert run.budgets.external_search_query_budget == 5
    assert run.budgets.rag_min_score == pytest.approx(0.3)


def test_create_run_budget_state_zeros():
    run = run_manager.create_run("Acme Corp", "logistics")
    bs = run.budget_state
    assert bs.external_search_queries_used == 0
    assert bs.external_search_calls_used == 0
    assert bs.rag_queries_used == 0


def test_get_run_returns_stored_run():
    run = run_manager.create_run("Acme Corp", "logistics")
    fetched = run_manager.get_run(run.run_id)
    assert fetched is not None
    assert fetched.run_id == run.run_id


def test_get_run_returns_none_for_unknown():
    result = run_manager.get_run("does-not-exist-xyz")
    assert result is None


def test_update_intake_transitions_to_intake():
    run = run_manager.create_run("Acme Corp", "logistics")
    intake = CompanyIntake(company_name="Acme Corp", industry="logistics")
    updated = run_manager.update_intake(run.run_id, intake)
    assert updated.status == RunStatus.INTAKE


def test_update_intake_stores_company_intake():
    run = run_manager.create_run("Acme Corp", "logistics")
    intake = CompanyIntake(
        company_name="Acme Corp",
        industry="logistics",
        employee_count_band="100-500",
    )
    updated = run_manager.update_intake(run.run_id, intake)
    assert updated.company_intake is not None
    assert updated.company_intake.company_name == "Acme Corp"
    assert updated.company_intake.employee_count_band == "100-500"


def test_transition_valid_created_to_intake():
    run = run_manager.create_run("Acme Corp", "logistics")
    updated = run_manager.transition(run.run_id, RunStatus.INTAKE)
    assert updated.status == RunStatus.INTAKE


def test_transition_invalid_raises_value_error():
    run = run_manager.create_run("Acme Corp", "logistics")
    with pytest.raises(ValueError, match="Invalid transition"):
        run_manager.transition(run.run_id, RunStatus.REASONING)


def test_transition_skip_stages_raises():
    run = run_manager.create_run("Acme Corp", "logistics")
    with pytest.raises(ValueError):
        run_manager.transition(run.run_id, RunStatus.PUBLISHED)


def test_transition_any_state_to_failed():
    run = run_manager.create_run("Acme Corp", "logistics")
    updated = run_manager.transition(run.run_id, RunStatus.FAILED)
    assert updated.status == RunStatus.FAILED
