"""API-specific request/response models.

Domain models live in core.schemas. This module holds models that exist
solely for the HTTP contract: enrichment requests, refinement requests,
and UI hint payloads.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel

from core.schemas import ReportFeedback  # noqa: F401 — used by ReportRefineRequest


# --- Enrichment ---
class EnrichmentCategory(str, Enum):
    TECHNOLOGY = "technology"
    FINANCIALS = "financials"
    OPERATIONS = "operations"
    PAIN_POINTS = "pain_points"
    CONSTRAINTS = "constraints"
    CORRECTIONS = "corrections"
    ADDITIONAL_CONTEXT = "additional_context"


class EnrichmentInput(BaseModel):
    category: EnrichmentCategory
    title: str
    detail: str
    affected_hypothesis_ids: list[str] = []
    confidence: float = 0.9


class EnrichRequest(BaseModel):
    inputs: list[EnrichmentInput]


class HypothesisDelta(BaseModel):
    hypothesis_id: str
    statement: str
    confidence_before: float
    confidence_after: float
    status_before: str
    status_after: str


class EnrichResponse(BaseModel):
    run_id: str
    evidence_added: int
    hypotheses_affected: int
    deltas: list[HypothesisDelta]
    message: str


# --- Refinement ---
class AssumptionCorrection(BaseModel):
    field: str
    new_value: str
    reason: Optional[str] = None


class RefineRequest(BaseModel):
    corrections: list[AssumptionCorrection] = []
    removed_opportunity_ids: list[str] = []
    additional_context: Optional[str] = None


class ReportRefineRequest(BaseModel):
    feedbacks: list[ReportFeedback]


# --- UI contract ---
class UIAction(BaseModel):
    id: str
    label: str
    endpoint: str
    method: str
    enabled: bool = True
    confirm: bool = False


class EditableField(BaseModel):
    path: str
    label: str
    field_type: str
    default: Optional[str] = None
    constraints: dict = {}


class BudgetView(BaseModel):
    rag_queries_remaining: int
    external_search_queries_remaining: int
    total_cost_estimate: str


class UIHints(BaseModel):
    stage_title: str
    stage_description: str
    progress: list[dict]
    actions: list[UIAction]
    editable_fields: list[EditableField]
    budget_view: BudgetView
    agent_message: Optional[str] = None
