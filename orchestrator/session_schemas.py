"""Session schemas for the Analyst Copilot conversational tool."""
from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


class ROICalibration(BaseModel):
    """Calibrated ROI estimate for a matched victory."""

    victory_metric: str = ""
    victory_savings: str = ""
    scale_factor: float = 1.0
    estimated_value: str = ""
    basis: str = ""
    confidence_note: str = ""


class VictoryAssessment(BaseModel):
    """Per-victory assessment with tier classification and ROI calibration."""

    victory_id: str = ""
    victory_title: str = ""
    tier: Literal["EASY_WIN", "MODERATE_WIN", "AMBITIOUS"] = "MODERATE_WIN"
    confidence: float = 0.5

    what_we_did: str = ""
    problem_fit: str = ""

    confirmed: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)

    calibration: ROICalibration | None = None
    adaptation_notes: str = ""
    key_question: str = ""


class TargetedQuestion(BaseModel):
    """A question the system wants to ask the analyst."""

    question: str = ""
    why: str = ""
    victory_id: str = ""
    field: str = ""


class Recommendations(BaseModel):
    """Three-tier recommendation summary."""

    easy_wins: list[VictoryAssessment] = Field(default_factory=list)
    moderate_wins: list[VictoryAssessment] = Field(default_factory=list)
    ambitious: list[VictoryAssessment] = Field(default_factory=list)
    total_estimated_value: str = ""
    top_questions: list[TargetedQuestion] = Field(default_factory=list)


class Turn(BaseModel):
    """One exchange in the conversation."""

    role: Literal["analyst", "system"] = "analyst"
    content: str = ""
    state_changes: dict = Field(default_factory=dict)


class ParsedInput(BaseModel):
    """Structured extraction from an analyst message."""

    company_name: str = ""
    industry: str = ""
    size_label: str = ""
    employee_count: int | None = None
    pain_points: list[str] = Field(default_factory=list)
    known_tech: list[str] = Field(default_factory=list)
    manual_processes: list[str] = Field(default_factory=list)
    context_notes: list[str] = Field(default_factory=list)
    explicit_queries: list[str] = Field(default_factory=list)
    generate_pitch: bool = False


class SessionState(BaseModel):
    """Accumulates across all turns in a conversation."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    dry_run: bool = False
    company_name: str = ""
    industry: str = ""
    size_label: str = ""
    employee_count: int | None = None

    pain_points: list[str] = Field(default_factory=list)
    known_tech: list[str] = Field(default_factory=list)
    manual_processes: list[str] = Field(default_factory=list)
    context_notes: list[str] = Field(default_factory=list)

    matched_victories: list[VictoryAssessment] = Field(default_factory=list)
    recommendations: Recommendations | None = None
    questions_pending: list[TargetedQuestion] = Field(default_factory=list)
    turn_history: list[Turn] = Field(default_factory=list)
