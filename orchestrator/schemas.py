"""Inter-agent contract schemas — all typed artifacts flow through these."""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

_KNOWN_INDUSTRIES = {
    "logistics", "healthcare", "financial_services", "retail", "insurance",
    "professional_services", "manufacturing", "energy", "real_estate",
    "construction", "ecommerce", "fintech",
}


class Signal(BaseModel):
    signal_id: str = ""
    type: Literal[
        "tech_stack", "data_signal", "ml_signal",
        "intent_signal", "ops_signal", "industry_hint", "scale_hint",
        "process_signal", "hiring_signal", "pain_point"
    ]
    value: str
    source: Literal["about_text", "job_posting", "product_page", "careers_page", "user_hint"]
    confidence: float = 1.0
    raw_quote: str = ""


class UserHints(BaseModel):
    """Optional consultant-provided context to enrich scraped signals."""

    pain_points: list[str] = Field(default_factory=list, max_length=5)
    known_tech: list[str] = Field(default_factory=list, max_length=10)
    industry: str = ""
    employee_count: int | None = None
    context: str = Field(default="", max_length=1000)

    @field_validator("pain_points", mode="before")
    @classmethod
    def _validate_pain_points(cls, v: list) -> list:
        result = []
        for item in v:
            item = item.strip()
            if len(item) < 10 or len(item) > 500:
                raise ValueError(
                    f"pain_point '{item[:30]}...' must be 10-500 chars"
                )
            result.append(item)
        return result

    @field_validator("known_tech", mode="before")
    @classmethod
    def _validate_known_tech(cls, v: list) -> list:
        result = []
        for item in v:
            item = item.strip()
            if len(item) < 2 or len(item) > 50:
                raise ValueError(
                    f"known_tech '{item}' must be 2-50 chars"
                )
            result.append(item)
        return result

    @field_validator("industry", mode="before")
    @classmethod
    def _validate_industry(cls, v: str) -> str:
        v = v.strip()
        if v and v not in _KNOWN_INDUSTRIES:
            raise ValueError(
                f"industry '{v}' not in known list: {sorted(_KNOWN_INDUSTRIES)}"
            )
        return v

    @field_validator("employee_count", mode="before")
    @classmethod
    def _validate_employee_count(cls, v: int | None) -> int | None:
        if v is not None and not (1 <= v <= 1_000_000):
            raise ValueError("employee_count must be 1-1000000")
        return v

    @field_validator("context", mode="before")
    @classmethod
    def _validate_context(cls, v: str) -> str:
        return v.strip()


class SignalSet(BaseModel):
    signals: list[Signal]
    industry: str = "unknown"
    scale: str = "unknown"
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    signal_count: int = 0


class DimensionScore(BaseModel):
    score: float
    signals_used: list[str] = []
    rationale: str = ""


class MaturityResult(BaseModel):
    dimensions: dict[str, DimensionScore]
    composite_score: float
    composite_label: str
    composite_rationale: str = ""


class ProvenMetrics(BaseModel):
    primary_label: str = ""
    primary_value: str = ""
    measurement_period: str = ""


class MatchResult(BaseModel):
    """Three-tier matching output — one schema covering DELIVERED, ADAPTATION, AMBITIOUS."""

    result_id: str = ""
    source_library: Literal["tenex_delivered", "industry_cases"] = "tenex_delivered"
    match_tier: Literal["DELIVERED", "ADAPTATION", "AMBITIOUS"]
    confidence: float = 0.5
    similarity_score: float = 0.0
    source_id: str = ""
    source_title: str = ""
    source_industry: str = ""
    relevance_note: str = ""
    # DELIVERED tier fields
    proven_metrics: ProvenMetrics | None = None
    client_profile_summary: str = ""
    engagement_duration: int | None = None
    tech_approach: str = ""
    gap_analysis: str | None = None
    # ADAPTATION tier fields
    base_solution_id: str = ""
    adaptation_notes: str = ""
    gap_from_base: float = 0.0
    estimated_scope_delta: str = ""
    adjusted_roi_range: str = ""
    # AMBITIOUS tier fields
    industry_examples: list[str] = []
    source_citations: list[str] = []
    deployment_scale: str = ""
    implementation_maturity: str = ""
    experimental_roi_range: str = ""


# Deprecated — kept for backwards compatibility. Use MatchResult for new code.
class VictoryMatch(BaseModel):
    win_id: str
    engagement_title: str
    match_tier: Literal["DIRECT_MATCH", "CALIBRATION_MATCH", "ADJACENT_MATCH"]
    relevance_note: str = ""
    roi_benchmark: str = ""
    industry: str = ""
    similarity_score: float = 0.0
    confidence: float = 0.5
    gap_analysis: str | None = None


class DataFlow(BaseModel):
    data_inputs: list[str] = []
    model_approach: str = ""
    output_consumer: str = ""
    feedback_loop: str = ""
    value_measurement: str = ""


class UseCase(BaseModel):
    tier: Literal["LOW_HANGING_FRUIT", "MEDIUM_SOLUTION", "HARD_EXPERIMENT"]
    title: str
    description: str = ""
    evidence_signal_ids: list[str] = []
    effort: Literal["Low", "Medium", "High"] = "Medium"
    impact: Literal["Low", "Medium", "High"] = "Medium"
    roi_estimate: str = ""
    roi_basis: str = ""
    rag_benchmark: str | None = None
    confidence: float = 0.5
    why_this_company: str = ""
    data_flow: DataFlow = Field(default_factory=DataFlow)
