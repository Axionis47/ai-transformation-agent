from __future__ import annotations

from fastapi import APIRouter, HTTPException

from core import run_manager
from core.schemas import (
    BudgetView,
    EditableField,
    Run,
    RunStatus,
    UIAction,
    UIHints,
)

router = APIRouter()

_ALL_STAGES = [
    RunStatus.CREATED,
    RunStatus.INTAKE,
    RunStatus.ASSUMPTIONS_DRAFT,
    RunStatus.ASSUMPTIONS_CONFIRMED,
    RunStatus.REASONING,
    RunStatus.SYNTHESIS,
    RunStatus.REPORT,
    RunStatus.PUBLISHED,
]


def _budget_view(run: Run) -> BudgetView:
    remaining_rag = run.budgets.rag_query_budget - run.budget_state.rag_queries_used
    remaining_search = (
        run.budgets.external_search_query_budget
        - run.budget_state.external_search_queries_used
    )
    return BudgetView(
        rag_queries_remaining=max(0, remaining_rag),
        external_search_queries_remaining=max(0, remaining_search),
        total_cost_estimate="$0.00",
    )


def _progress(current: RunStatus) -> list[dict]:
    progress = []
    for stage in _ALL_STAGES:
        if stage == current:
            status = "active"
        elif _ALL_STAGES.index(stage) < _ALL_STAGES.index(current):
            status = "completed"
        else:
            status = "pending"
        progress.append({"stage": stage.value, "status": status})
    return progress


def _intake_hints(run: Run, bv: BudgetView, prog: list[dict]) -> UIHints:
    return UIHints(
        stage_title="Company Intake",
        stage_description="Provide company details to begin the analysis.",
        progress=prog,
        actions=[
            UIAction(
                id="submit_intake",
                label="Submit Company Info",
                endpoint=f"/v1/runs/{run.run_id}/company-intake",
                method="PUT",
            )
        ],
        editable_fields=[
            EditableField(path="company_name", label="Company Name", field_type="text"),
            EditableField(path="industry", label="Industry", field_type="text"),
            EditableField(path="employee_count_band", label="Company Size", field_type="select"),
            EditableField(path="notes", label="Additional Notes", field_type="text"),
        ],
        budget_view=bv,
    )


def _assumptions_draft_hints(run: Run, bv: BudgetView, prog: list[dict]) -> UIHints:
    fields: list[EditableField] = []
    if run.assumptions:
        for a in run.assumptions.assumptions:
            fields.append(
                EditableField(
                    path=f"assumptions.{a.field}",
                    label=a.field.replace("_", " ").title(),
                    field_type="text",
                    default=a.value,
                )
            )
    return UIHints(
        stage_title="Review Assumptions",
        stage_description="Review and confirm or edit the generated assumptions.",
        progress=prog,
        actions=[
            UIAction(
                id="confirm_assumptions",
                label="Confirm Assumptions",
                endpoint=f"/v1/runs/{run.run_id}/assumptions/confirm",
                method="POST",
            ),
            UIAction(
                id="edit_assumptions",
                label="Edit Assumptions",
                endpoint=f"/v1/runs/{run.run_id}/assumptions",
                method="PUT",
            ),
        ],
        editable_fields=fields,
        budget_view=bv,
    )
