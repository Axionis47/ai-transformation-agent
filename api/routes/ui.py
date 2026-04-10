from __future__ import annotations

from fastapi import APIRouter, HTTPException

from core import run_manager
from core.schemas import (
    Run,
    RunStatus,
)
from api.schemas import (
    BudgetView,
    EditableField,
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
    remaining_search = run.budgets.external_search_query_budget - run.budget_state.external_search_queries_used
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


def _build_ui_hints(run: Run) -> UIHints:
    status = run.status
    bv = _budget_view(run)
    prog = _progress(status)

    if status == RunStatus.CREATED:
        return _intake_hints(run, bv, prog)

    if status == RunStatus.INTAKE:
        return UIHints(
            stage_title="Generating Assumptions",
            stage_description="Intake saved. Start analysis to generate assumptions.",
            progress=prog,
            actions=[
                UIAction(
                    id="start_analysis", label="Start Analysis", endpoint=f"/v1/runs/{run.run_id}/start", method="POST"
                )
            ],
            editable_fields=[],
            budget_view=bv,
        )

    if status == RunStatus.ASSUMPTIONS_DRAFT:
        return _assumptions_draft_hints(run, bv, prog)

    if status == RunStatus.ASSUMPTIONS_CONFIRMED:
        return UIHints(
            stage_title="Assumptions Confirmed",
            stage_description="Starting reasoning phase.",
            progress=prog,
            actions=[],
            editable_fields=[],
            budget_view=bv,
        )

    if status == RunStatus.REASONING:
        return UIHints(
            stage_title="Agent Reasoning",
            stage_description="The agent is reasoning over your company data.",
            progress=prog,
            actions=[
                UIAction(
                    id="answer_question",
                    label="Answer Question",
                    endpoint=f"/v1/runs/{run.run_id}/answer",
                    method="POST",
                )
            ],
            editable_fields=[],
            budget_view=bv,
            agent_message=None,
        )

    if status == RunStatus.SYNTHESIS:
        return UIHints(
            stage_title="Synthesising Opportunities",
            stage_description="Synthesising findings into opportunities.",
            progress=prog,
            actions=[],
            editable_fields=[],
            budget_view=bv,
        )

    if status == RunStatus.REPORT:
        return UIHints(
            stage_title="Report Ready",
            stage_description="Your opportunity report is ready to publish.",
            progress=prog,
            actions=[
                UIAction(
                    id="publish_report",
                    label="Publish Report",
                    endpoint=f"/v1/runs/{run.run_id}/publish",
                    method="POST",
                    confirm=True,
                )
            ],
            editable_fields=[],
            budget_view=bv,
        )

    return UIHints(
        stage_title="Published" if status == RunStatus.PUBLISHED else "Failed",
        stage_description=("Report published." if status == RunStatus.PUBLISHED else "The run encountered an error."),
        progress=prog,
        actions=[
            UIAction(id="view_report", label="View Report", endpoint=f"/v1/runs/{run.run_id}/report", method="GET")
        ],
        editable_fields=[],
        budget_view=bv,
    )


@router.get("/runs/{run_id}/ui", response_model=UIHints)
def get_ui_hints(run_id: str) -> UIHints:
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return _build_ui_hints(run)
