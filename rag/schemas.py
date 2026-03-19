"""RAG record schemas — validates Library A (solutions) and Library B (industry cases)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CompanyProfileSchema(BaseModel):
    size_employees: int = 0
    size_label: str = ""
    annual_revenue_usd: str = ""
    geography: str = ""
    business_model: str = ""


class PrimaryMetricSchema(BaseModel):
    label: str = ""
    value: str = ""
    baseline: str = ""
    outcome: str = ""


class ResultsSchema(BaseModel):
    primary_metric: PrimaryMetricSchema = Field(default_factory=PrimaryMetricSchema)
    secondary_metrics: list[dict] = []
    measurement_period: str = ""
    measurement_basis: str = ""


class EngagementDetailsSchema(BaseModel):
    duration_months: int = 0
    tenex_team_size: int = 0
    tenex_roles: list[str] = []
    client_team_involvement: str = ""
    delivery_model: str = ""


class TechStackSchema(BaseModel):
    data_sources: list[str] = []
    ml_approach: str = ""
    infrastructure: list[str] = []
    client_systems_integrated: list[str] = []


SolutionCategory = Literal[
    "predictive_model",
    "classification",
    "nlp",
    "computer_vision",
    "optimization",
    "scoring_model",
]


class SolutionSchema(BaseModel):
    """Validates a Library A record (Tenex delivered solution)."""

    id: str
    engagement_title: str
    industry: str
    sector_tags: list[str] = []
    company_profile: CompanyProfileSchema = Field(default_factory=CompanyProfileSchema)
    problem_statement: str = ""
    solution_summary: str = ""
    results: ResultsSchema = Field(default_factory=ResultsSchema)
    engagement_details: EngagementDetailsSchema = Field(
        default_factory=EngagementDetailsSchema
    )
    tech_stack: TechStackSchema = Field(default_factory=TechStackSchema)
    maturity_at_engagement: str = ""
    follow_on_engagement: bool = False
    lessons_learned: str = ""
    embed_text: str = ""
    industry_benchmark: str = ""
    success_threshold: str = ""
    gap_analysis_template: str = ""
    # Sprint 8 new fields — defaults allow existing records to pass validation
    status: Literal["draft", "active", "deprecated"] = "active"
    ingestion_date: str = ""
    solution_category: SolutionCategory = "predictive_model"
    applicable_signals: list[str] = []


class CaseCompanyProfileSchema(BaseModel):
    company_name: str = ""
    company_type: str = ""
    geography: str = ""
    size_hint: str = ""


class AiApplicationSchema(BaseModel):
    problem_addressed: str = ""
    solution_description: str = ""
    technology_used: list[str] = []
    deployment_scale: str = ""
    implementation_year: int = 0


class ReportedOutcomesSchema(BaseModel):
    headline_metric: str = ""
    supporting_metrics: list[str] = []
    source: str = ""
    confidence_in_data: Literal["high", "medium", "low"] = "medium"


class IndustryCaseStudySchema(BaseModel):
    """Validates a Library B record (external market intelligence)."""

    id: str
    case_title: str
    industry: str
    sector_tags: list[str] = []
    company_profile: CaseCompanyProfileSchema = Field(
        default_factory=CaseCompanyProfileSchema
    )
    ai_application: AiApplicationSchema = Field(default_factory=AiApplicationSchema)
    reported_outcomes: ReportedOutcomesSchema = Field(
        default_factory=ReportedOutcomesSchema
    )
    maturity_signal: str = ""
    use_case_category: SolutionCategory = "predictive_model"
    applicable_signals: list[str] = []
    embed_text: str = ""
    status: Literal["draft", "active", "deprecated"] = "active"
    ingestion_date: str = ""
