"""Tests for core/schemas.py — Pydantic model validation."""

from datetime import datetime, timezone

import pytest

from core.schemas import (
    BudgetConfig,
    BudgetState,
    CompanyIntake,
    EvidenceItem,
    EvidenceSource,
    Opportunity,
    OpportunityTier,
    Run,
    RunStatus,
)
from api.schemas import (
    BudgetView,
    EditableField,
    UIAction,
    UIHints,
)


def _make_budget_config() -> BudgetConfig:
    return BudgetConfig(
        external_search_query_budget=5,
        external_search_max_calls=3,
        rag_query_budget=8,
        rag_top_k=5,
        rag_min_score=0.3,
    )


def _make_run() -> Run:
    return Run(
        run_id="run-001",
        status=RunStatus.CREATED,
        created_at=datetime.now(timezone.utc),
        config_snapshot={"budgets": {}, "models": {}},
        budgets=_make_budget_config(),
        budget_state=BudgetState(),
    )


def test_run_creation_required_fields():
    run = _make_run()
    assert run.run_id == "run-001"
    assert run.status == RunStatus.CREATED
    assert run.company_intake is None
    assert run.assumptions is None
    assert isinstance(run.budget_state, BudgetState)


def test_company_intake_required_only():
    intake = CompanyIntake(company_name="Acme", industry="logistics")
    assert intake.employee_count_band is None
    assert intake.notes is None
    assert intake.constraints == []


def test_company_intake_all_fields():
    intake = CompanyIntake(
        company_name="Acme",
        industry="logistics",
        employee_count_band="100-500",
        notes="Looking to automate dispatch",
        constraints=["no cloud", "EU data only"],
    )
    assert intake.employee_count_band == "100-500"
    assert len(intake.constraints) == 2


def test_evidence_item_wins_kb():
    item = EvidenceItem(
        evidence_id="ev-001",
        run_id="run-001",
        source_type=EvidenceSource.WINS_KB,
        source_ref="chunk-42",
        title="Logistics automation win",
        snippet="Reduced dispatch time by 40%",
        relevance_score=0.85,
    )
    assert item.source_type == EvidenceSource.WINS_KB
    assert item.uri is None
    assert item.retrieval_meta == {}


def test_evidence_item_google_search():
    item = EvidenceItem(
        evidence_id="ev-002",
        run_id="run-001",
        source_type=EvidenceSource.GOOGLE_SEARCH,
        source_ref="grounding-uri-abc",
        title="Industry report",
        uri="https://example.com/report",
        snippet="AI adoption rising in logistics",
        relevance_score=0.72,
        confidence_score=0.9,
    )
    assert item.source_type == EvidenceSource.GOOGLE_SEARCH
    assert item.uri == "https://example.com/report"
    assert item.confidence_score == 0.9


def test_opportunity_easy_tier():
    opp = Opportunity(
        opportunity_id="opp-001",
        run_id="run-001",
        template_id="tmpl-route-opt",
        name="Route Optimisation",
        description="Automate route planning",
        tier=OpportunityTier.EASY,
        feasibility=0.9,
        roi=0.8,
        time_to_value=0.85,
        confidence=0.87,
        evidence_ids=["ev-001"],
        assumptions={"workflow": "manual dispatch"},
        rationale="Direct match to past win",
    )
    assert opp.tier == OpportunityTier.EASY
    assert opp.adaptation_needed is None
    assert opp.risks == []


def test_opportunity_medium_tier():
    opp = Opportunity(
        opportunity_id="opp-002",
        run_id="run-001",
        template_id="tmpl-doc-processing",
        name="Document Processing",
        description="Automate invoice handling",
        tier=OpportunityTier.MEDIUM,
        feasibility=0.7,
        roi=0.65,
        time_to_value=0.6,
        confidence=0.7,
        evidence_ids=["ev-001", "ev-002"],
        assumptions={"volume": "high"},
        rationale="Needs adaptation for industry",
        adaptation_needed="Retrain on logistics invoices",
    )
    assert opp.tier == OpportunityTier.MEDIUM
    assert opp.adaptation_needed == "Retrain on logistics invoices"


def test_opportunity_hard_tier():
    opp = Opportunity(
        opportunity_id="opp-003",
        run_id="run-001",
        template_id="tmpl-novel",
        name="Predictive Demand",
        description="Predict demand spikes",
        tier=OpportunityTier.HARD,
        feasibility=0.4,
        roi=0.9,
        time_to_value=0.3,
        confidence=0.5,
        evidence_ids=[],
        assumptions={},
        rationale="Ambitious, novel application",
        risks=["data quality", "model drift"],
    )
    assert opp.tier == OpportunityTier.HARD
    assert len(opp.risks) == 2


def test_uihints_serializes():
    bv = BudgetView(
        rag_queries_remaining=8,
        external_search_queries_remaining=5,
        total_cost_estimate="$0.00",
    )
    hints = UIHints(
        stage_title="Company Intake",
        stage_description="Provide details.",
        progress=[{"stage": "created", "status": "active"}],
        actions=[UIAction(id="submit_intake", label="Submit", endpoint="/v1/runs/x/company-intake", method="PUT")],
        editable_fields=[EditableField(path="company_name", label="Company Name", field_type="text")],
        budget_view=bv,
    )
    data = hints.model_dump()
    assert data["stage_title"] == "Company Intake"
    assert data["agent_message"] is None
    assert isinstance(data["progress"], list)
    assert isinstance(data["actions"], list)


def test_budget_config_validation():
    bc = _make_budget_config()
    assert bc.external_search_query_budget == 5
    assert bc.rag_min_score == 0.3


def test_run_status_enum_values():
    assert RunStatus.CREATED.value == "created"
    assert RunStatus.INTAKE.value == "intake"
    assert RunStatus.REASONING.value == "reasoning"
    assert RunStatus.FAILED.value == "failed"
    assert RunStatus.PUBLISHED.value == "published"
