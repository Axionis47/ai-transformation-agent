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


class UserQuestion(BaseModel):
    question_id: str
    run_id: str
    field: str
    question_text: str
    context: Optional[str] = None


class UserAnswer(BaseModel):
    question_id: str
    answer_text: str


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
    evidence: list["EvidenceItem"] = []
    reasoning_state: Optional[ReasoningState] = None
    opportunities: list["Opportunity"] = []
    report: dict = {}


# --- Reasoning ---
class ReasoningState(BaseModel):
    current_loop: int = 0
    evidence_ids: list[str] = []
    field_coverage: dict[str, float] = {}
    overall_confidence: float = 0.0
    pending_question: Optional["UserQuestion"] = None
    completed: bool = False
    stop_reason: Optional[str] = None
    coverage_gaps: list[str] = []
    loops_completed: int = 0
    escalation_reason: Optional[str] = None
    escalation_fields: list[str] = []
    contradictions: list[dict] = []
    confidence_history: list[float] = []


class ReasoningLoopResult(BaseModel):
    completed: bool
    loops_run: int
    evidence_items: list["EvidenceItem"]
    field_coverage: dict[str, float]
    overall_confidence: float
    pending_question: Optional["UserQuestion"] = None
    stop_reason: Optional[str] = None
    coverage_gaps: list[str] = []
    escalation_reason: Optional[str] = None
    escalation_fields: list[str] = []
    contradictions: list[dict] = []
    confidence_history: list[float] = []


# --- Evidence ---
class EvidenceSource(str, Enum):
    WINS_KB = "wins_kb"
    GOOGLE_SEARCH = "google_search"
    USER_PROVIDED = "user_provided"


class Provenance(BaseModel):
    source_evidence_ids: list[str] = []
    extraction_timestamp: Optional[datetime] = None
    source_type: str = "raw"  # "raw" | "summarized" | "inferred"
    confidence: float = 0.0


class EvidenceItem(BaseModel):
    evidence_id: str
    run_id: str
    source_type: EvidenceSource
    source_ref: str
    title: str
    uri: Optional[str] = None
    snippet: str
    relevance_score: float
    confidence_score: Optional[float] = None
    retrieval_meta: dict = {}
    provenance: Optional[Provenance] = None


# --- Opportunity ---
class OpportunityTier(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Opportunity(BaseModel):
    opportunity_id: str
    run_id: str
    template_id: str
    name: str
    description: str
    tier: OpportunityTier
    feasibility: float
    roi: float
    time_to_value: float
    confidence: float
    evidence_ids: list[str]
    assumptions: dict
    rationale: str
    adaptation_needed: Optional[str] = None
    risks: list[str] = []
    data_sufficiency: str = "scored"


# --- Stage output ---
class StageOutput(BaseModel):
    run_id: str
    stage_name: str
    version: int = 1
    created_at: datetime
    payload: dict


# --- Trace event ---
class TraceEvent(BaseModel):
    event_id: str
    run_id: str
    timestamp: datetime
    event_type: str
    payload: dict = {}


# --- Confidence ---
class FieldConfidence(BaseModel):
    field: str
    evidence_coverage: float
    evidence_strength: float
    source_diversity: float
    confidence: float


class SectionConfidence(BaseModel):
    section: str
    field_confidences: list[FieldConfidence]
    missing_fields: list[str]
    confidence: float


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
