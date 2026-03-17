"""Inter-agent contract schemas — all typed artifacts flow through these."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Signal(BaseModel):
    signal_id: str = ""
    type: Literal[
        "tech_stack", "data_signal", "ml_signal",
        "intent_signal", "ops_signal", "industry_hint", "scale_hint",
        "process_signal", "hiring_signal", "pain_point"
    ]
    value: str
    source: Literal["about_text", "job_posting", "product_page", "careers_page"]
    confidence: float = 1.0
    raw_quote: str = ""


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
