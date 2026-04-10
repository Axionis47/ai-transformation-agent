from __future__ import annotations

import uuid
from datetime import datetime, timezone

from core.config import freeze_config
from core.events import EventType
from core.schemas import (
    BudgetConfig,
    BudgetState,
    CompanyIntake,
    Run,
    RunStatus,
)
from services import trace
from services.storage.memory_store import MemoryStore
from services.storage.protocol import StorageProtocol

# Storage backend — swappable via init_storage()
_store: StorageProtocol = MemoryStore()


def init_storage(store: StorageProtocol) -> None:
    """Swap the storage backend. Call at app startup."""
    global _store
    _store = store


def get_storage() -> StorageProtocol:
    """Get current storage backend (for direct access if needed)."""
    return _store


VALID_TRANSITIONS: dict[RunStatus, list[RunStatus]] = {
    # Legacy linear pipeline (still works with orchestration.mode=legacy)
    RunStatus.CREATED: [RunStatus.INTAKE, RunStatus.FAILED],
    RunStatus.INTAKE: [RunStatus.ASSUMPTIONS_DRAFT, RunStatus.GROUNDING, RunStatus.FAILED],
    RunStatus.ASSUMPTIONS_DRAFT: [RunStatus.ASSUMPTIONS_CONFIRMED, RunStatus.FAILED],
    RunStatus.ASSUMPTIONS_CONFIRMED: [RunStatus.REASONING, RunStatus.GROUNDING, RunStatus.FAILED],
    RunStatus.REASONING: [RunStatus.SYNTHESIS, RunStatus.FAILED],
    RunStatus.SYNTHESIS: [RunStatus.REPORT, RunStatus.FAILED],
    RunStatus.REPORT: [RunStatus.REVIEW, RunStatus.PUBLISHED, RunStatus.FAILED],
    # Multi-agent pipeline (with backtracking)
    RunStatus.GROUNDING: [RunStatus.DEEP_RESEARCH, RunStatus.FAILED],
    RunStatus.DEEP_RESEARCH: [RunStatus.HYPOTHESIS_FORMATION, RunStatus.GROUNDING, RunStatus.FAILED],
    RunStatus.HYPOTHESIS_FORMATION: [RunStatus.HYPOTHESIS_TESTING, RunStatus.DEEP_RESEARCH, RunStatus.FAILED],
    RunStatus.HYPOTHESIS_TESTING: [
        RunStatus.SYNTHESIS,
        RunStatus.HYPOTHESIS_FORMATION,
        RunStatus.DEEP_RESEARCH,
        RunStatus.FAILED,
    ],
    RunStatus.REVIEW: [RunStatus.PUBLISHED, RunStatus.HYPOTHESIS_TESTING, RunStatus.DEEP_RESEARCH, RunStatus.FAILED],
}


def _persist(run: Run) -> Run:
    """Save run to storage after every mutation."""
    _store.save_run(run)
    return run


def create_run(
    company_name: str,
    industry: str,
    config_overrides: dict | None = None,
) -> Run:
    run_id = str(uuid.uuid4())
    config_snapshot = freeze_config(config_overrides)
    budgets = BudgetConfig(**config_snapshot["budgets"])

    run = Run(
        run_id=run_id,
        status=RunStatus.CREATED,
        created_at=datetime.now(timezone.utc),
        config_snapshot=config_snapshot,
        budgets=budgets,
        budget_state=BudgetState(),
    )

    trace.emit(run_id, EventType.RUN_CREATED, {"company_name": company_name, "industry": industry})
    trace.emit(run_id, EventType.CONFIG_SNAPSHOT_SAVED, {"snapshot_keys": list(config_snapshot.keys())})
    return _persist(run)


def get_run(run_id: str) -> Run | None:
    return _store.get_run(run_id)


def list_runs(limit: int = 50, offset: int = 0) -> list[Run]:
    return _store.list_runs(limit=limit, offset=offset)


def update_intake(run_id: str, intake: CompanyIntake) -> Run:
    run = _require_run(run_id)
    run.company_intake = intake
    run.status = RunStatus.INTAKE
    trace.emit(run_id, EventType.COMPANY_INTAKE_SAVED, {"company_name": intake.company_name})
    return _persist(run)


def transition(run_id: str, new_status: RunStatus) -> Run:
    run = _require_run(run_id)
    allowed = VALID_TRANSITIONS.get(run.status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Invalid transition: {run.status.value} -> {new_status.value}. Allowed: {[s.value for s in allowed]}"
        )
    run.status = new_status
    return _persist(run)


def _require_run(run_id: str) -> Run:
    run = _store.get_run(run_id)
    if run is None:
        raise ValueError(f"Run not found: {run_id}")
    return run
