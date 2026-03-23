from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


# --- Company intake ---
class CompanyIntake(BaseModel):
    company_name: str
    industry: str
    employee_count_band: Optional[str] = None
    notes: Optional[str] = None
    constraints: list[str] = []


# --- Assumptions ---
class Assumption(BaseModel):
    field: str
    value: str
    confidence: float
    source: str  # "grounding" | "user" | "inferred"


class AssumptionsDraft(BaseModel):
    assumptions: list[Assumption]
    open_questions: list[str]


# --- Run ---
class BudgetConfig(BaseModel):
    external_search_query_budget: int
    external_search_max_calls: int
    rag_query_budget: int
    rag_top_k: int
    rag_min_score: float


class BudgetState(BaseModel):
    external_search_queries_used: int = 0
    external_search_calls_used: int = 0
    rag_queries_used: int = 0


class RunStatus(str, Enum):
    CREATED = "created"
    INTAKE = "intake"
    ASSUMPTIONS_DRAFT = "assumptions_draft"
    ASSUMPTIONS_CONFIRMED = "assumptions_confirmed"
    REASONING = "reasoning"
    SYNTHESIS = "synthesis"
    REPORT = "report"
    PUBLISHED = "published"
    FAILED = "failed"


class Run(BaseModel):
    run_id: str
    status: RunStatus
    created_at: datetime
    config_snapshot: dict
    budgets: BudgetConfig
    budget_state: BudgetState
    company_intake: Optional[CompanyIntake] = None
    assumptions: Optional[AssumptionsDraft] = None
