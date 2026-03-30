from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class ChunkType(str, Enum):
    """Each engagement is split into these independently retrievable facets."""

    PROBLEM_PATTERN = "problem_pattern"
    SOLUTION_APPROACH = "solution_approach"
    PRECONDITIONS = "preconditions"
    OUTCOMES = "outcomes"
    DISCOVERY_INSIGHT = "discovery_insight"
    IMPLEMENTATION_FRICTION = "implementation_friction"
    GENERALIZATION = "generalization"


ALL_CHUNK_TYPES = list(ChunkType)
CHUNK_TYPE_COUNT = len(ALL_CHUNK_TYPES)


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
    # Engagement economics
    engagement_value_usd: int = 0
    team_composition: str = ""
    buyer_persona: str = ""
    trigger_event: str = ""
    # Analyst case notebook fields
    solution_description: str = ""
    outcome_narrative: str = ""
    generalized_for: str = ""
    lessons_learned: list[str] = []
    discovery_insight: str = ""
    implementation_friction: list[str] = []
    baseline_metrics: dict = {}
