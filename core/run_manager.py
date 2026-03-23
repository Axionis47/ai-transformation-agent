from __future__ import annotations

import uuid
from datetime import datetime, timezone

from core.config import freeze_config
from core.events import EventType
from core.schemas import BudgetConfig, BudgetState, CompanyIntake, Run, RunStatus
from services import trace

_runs: dict[str, Run] = {}

VALID_TRANSITIONS: dict[RunStatus, list[RunStatus]] = {
    RunStatus.CREATED: [RunStatus.INTAKE, RunStatus.FAILED],
    RunStatus.INTAKE: [RunStatus.ASSUMPTIONS_DRAFT, RunStatus.FAILED],
    RunStatus.ASSUMPTIONS_DRAFT: [RunStatus.ASSUMPTIONS_CONFIRMED, RunStatus.FAILED],
    RunStatus.ASSUMPTIONS_CONFIRMED: [RunStatus.REASONING, RunStatus.FAILED],
    RunStatus.REASONING: [RunStatus.SYNTHESIS, RunStatus.FAILED],
    RunStatus.SYNTHESIS: [RunStatus.REPORT, RunStatus.FAILED],
    RunStatus.REPORT: [RunStatus.PUBLISHED, RunStatus.FAILED],
}


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
    _runs[run_id] = run

    trace.emit(run_id, EventType.RUN_CREATED, {"company_name": company_name, "industry": industry})
    trace.emit(run_id, EventType.CONFIG_SNAPSHOT_SAVED, {"snapshot_keys": list(config_snapshot.keys())})
    return run


def get_run(run_id: str) -> Run | None:
    return _runs.get(run_id)


def update_intake(run_id: str, intake: CompanyIntake) -> Run:
    run = _require_run(run_id)
    run.company_intake = intake
    run.status = RunStatus.INTAKE
    trace.emit(run_id, EventType.COMPANY_INTAKE_SAVED, {"company_name": intake.company_name})
    return run


def transition(run_id: str, new_status: RunStatus) -> Run:
    run = _require_run(run_id)
    allowed = VALID_TRANSITIONS.get(run.status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Invalid transition: {run.status.value} -> {new_status.value}. "
            f"Allowed: {[s.value for s in allowed]}"
        )
    run.status = new_status
    return run


def _require_run(run_id: str) -> Run:
    run = _runs.get(run_id)
    if run is None:
        raise ValueError(f"Run not found: {run_id}")
    return run
