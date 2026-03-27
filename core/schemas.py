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
    total_tool_calls_used: int = 0


class RunStatus(str, Enum):
    CREATED = "created"
    INTAKE = "intake"
    ASSUMPTIONS_DRAFT = "assumptions_draft"
    ASSUMPTIONS_CONFIRMED = "assumptions_confirmed"
    GROUNDING = "grounding"
    DEEP_RESEARCH = "deep_research"
    HYPOTHESIS_FORMATION = "hypothesis_formation"
    HYPOTHESIS_TESTING = "hypothesis_testing"
    REASONING = "reasoning"
    SYNTHESIS = "synthesis"
    REPORT = "report"
    REVIEW = "review"
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
    working_memory: dict[str, "FieldKnowledge"] = {}
    hypotheses_legacy: list[str] = []  # old field, kept for backward compat
    opportunities: list["Opportunity"] = []
    report: dict = {}
    # --- Multi-agent fields ---
    company_understanding: Optional["CompanyUnderstanding"] = None
    industry_context: Optional["IndustryContext"] = None
    pain_points: list["PainPoint"] = []
    hypotheses: list["Hypothesis"] = []
    agent_states: list["AgentState"] = []
    user_interactions: list["UserInteractionPoint"] = []
    spawn_requests: list["SpawnRequest"] = []
    derived_insights: list["DerivedInsight"] = []
    phase_briefings: dict[str, str] = {}  # phase_name -> compressed briefing
    adaptive_report: Optional["AdaptiveReport"] = None
    feedback_history: list["ReportFeedback"] = []


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
    produced_by: str = ""  # which agent produced this evidence


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


# --- Report feedback ---
class ReportFeedback(BaseModel):
    feedback_type: str  # "edit" | "deepen" | "reinvestigate"
    target_section: str  # "executive_summary" | "opportunity:{hyp_id}" | "unknowns" | "next_steps" | "confidence"
    instruction: str  # user's specific feedback text


class ReportRefineRequest(BaseModel):
    feedbacks: list[ReportFeedback]


# --- Refinement ---
class AssumptionCorrection(BaseModel):
    field: str
    new_value: str
    reason: Optional[str] = None


class RefineRequest(BaseModel):
    corrections: list[AssumptionCorrection] = []
    removed_opportunity_ids: list[str] = []
    additional_context: Optional[str] = None


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
class FieldKnowledge(BaseModel):
    """Per-field synthesized understanding, updated each reasoning loop."""
    field: str
    synthesis: str = ""
    evidence_ids: list[str] = []
    confidence: float = 0.0
    last_updated_loop: int = -1


# --- Multi-agent hypothesis system ---
class HypothesisStatus(str, Enum):
    FORMING = "forming"
    TESTING = "testing"
    VALIDATED = "validated"
    REJECTED = "rejected"
    NEEDS_USER_INPUT = "needs_user_input"


class TestResult(BaseModel):
    test_type: str  # "evidence_search" | "analogous_case" | "counter_evidence"
    finding: str
    impact_on_confidence: float
    evidence_ids: list[str] = []


class Hypothesis(BaseModel):
    hypothesis_id: str
    statement: str
    category: str  # "automation" | "copilot" | "decision_support" | "optimization"
    target_process: str
    status: HypothesisStatus = HypothesisStatus.FORMING
    confidence: float = 0.0
    evidence_for: list[str] = []
    evidence_against: list[str] = []
    evidence_conditions: list[str] = []  # prerequisite/caveat evidence
    analogous_engagements: list[str] = []
    conditions_for_success: list[str] = []
    risks: list[str] = []
    open_questions: list[str] = []
    test_results: list[TestResult] = []
    reasoning_chain: list["ReasoningStep"] = []  # full causal chain
    formed_by_agent: str = ""
    tested_by_agent: str = ""
    parent_hypothesis_id: Optional[str] = None


class CompanyUnderstanding(BaseModel):
    company_name: str
    what_they_do: str = ""
    how_they_make_money: str = ""
    size_and_scale: str = ""
    technology_landscape: str = ""
    organizational_structure: str = ""
    confidence: float = 0.0
    evidence_ids: list[str] = []


class IndustryContext(BaseModel):
    industry: str
    key_trends: list[str] = []
    competitive_dynamics: str = ""
    regulatory_landscape: str = ""
    ai_adoption_level: str = ""
    confidence: float = 0.0
    evidence_ids: list[str] = []


class PainPoint(BaseModel):
    pain_id: str
    description: str
    affected_process: str
    severity: str = "medium"  # "high" | "medium" | "low"
    current_workaround: str = ""
    evidence_ids: list[str] = []
    confidence: float = 0.0


class AgentState(BaseModel):
    agent_id: str
    agent_type: str
    status: str = "pending"  # "pending" | "running" | "completed" | "failed" | "waiting_user"
    tool_calls_made: int = 0
    tool_calls_budget: int = 0
    evidence_produced: list[str] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    summary: str = ""


class SpawnRequest(BaseModel):
    requesting_agent: str
    reason: str
    suggested_hypothesis: str
    priority: str = "medium"  # "high" | "medium" | "low"


class UserInteractionPoint(BaseModel):
    interaction_id: str
    run_id: str
    interaction_type: str  # "interesting_finding" | "confirmation" | "ambiguity"
    message: str
    context: dict = {}
    agent_source: str = ""
    requires_response: bool = True
    response: Optional[str] = None


class ReportOpportunity(BaseModel):
    title: str
    hypothesis_id: str
    narrative: str
    tier: str  # "easy" | "medium" | "hard"
    confidence: float = 0.0
    roi_estimate: Optional[dict] = None
    evidence_summary: str = ""
    analogous_cases: list[dict] = []
    risks: list[str] = []
    conditions_for_success: list[str] = []
    recommended_approach: str = ""


class AdaptiveReport(BaseModel):
    run_id: str
    executive_summary: str = ""
    key_insight: str = ""
    opportunities: list[ReportOpportunity] = []
    reasoning_chain: list[str] = []
    confidence_assessment: str = ""
    what_we_dont_know: list[str] = []
    recommended_next_steps: list[str] = []
    evidence_annex: list[dict] = []
    agent_activity_summary: list[dict] = []


class ReasoningStep(BaseModel):
    """One step in a hypothesis's causal reasoning chain."""
    step_type: str  # "formed_because" | "tested_with" | "contradicted_by" | "revised_because" | "validated_by"
    description: str
    evidence_ids: list[str] = []
    confidence_delta: float = 0.0
    timestamp: Optional[datetime] = None


class DerivedInsight(BaseModel):
    """A conclusion drawn from evidence — not raw evidence itself."""
    insight_id: str
    phase: str  # which phase produced this
    statement: str  # "Their dispatch is manual, costing ~15% efficiency"
    supporting_evidence_ids: list[str] = []
    confidence: float = 0.0
    produced_by_agent: str = ""


class AgentScope(str, Enum):
    """Controls what context an agent can see."""
    COMPANY_PROFILER = "company_profiler"
    INDUSTRY_ANALYST = "industry_analyst"
    PAIN_INVESTIGATOR = "pain_investigator"
    HYPOTHESIS_FORMER = "hypothesis_former"
    HYPOTHESIS_TESTER = "hypothesis_tester"
    REPORT_SYNTHESIZER = "report_synthesizer"


class AgentResult(BaseModel):
    """Typed result returned by every research agent to the orchestrator."""
    agent_id: str
    agent_type: str
    success: bool = True
    evidence_items: list["EvidenceItem"] = []
    summary: str = ""
    spawn_requests: list[SpawnRequest] = []
    error: Optional[str] = None
    derived_insights: list["DerivedInsight"] = []  # conclusions drawn from evidence
    # Domain-specific outputs (one will be populated per agent type)
    company_understanding: Optional[CompanyUnderstanding] = None
    industry_context: Optional[IndustryContext] = None
    pain_points: list[PainPoint] = []
    hypotheses: list[Hypothesis] = []
    adaptive_report: Optional[AdaptiveReport] = None


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
