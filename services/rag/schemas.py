from __future__ import annotations

from pydantic import BaseModel


class EngagementCase(BaseModel):
    engagement_id: str
    title: str
    industry: str
    company_size_band: str
    problem: str
    workflow_area: str  # support | finance_ops | rev_ops | operations
    solution_shape: str  # copilot | automation | decision_support
    tech_stack: list[str]
    timeline_weeks: int
    measured_impact: dict
    roi_drivers: list[str]
    conditions_for_success: list[str]
    anti_patterns: list[str]
    tags: list[str]
    # Analyst case notebook fields
    generalized_for: str = ""
    lessons_learned: list[str] = []
    discovery_insight: str = ""
    implementation_friction: list[str] = []
    baseline_metrics: dict = {}
