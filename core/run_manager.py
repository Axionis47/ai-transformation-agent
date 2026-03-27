from __future__ import annotations

import uuid
from datetime import datetime, timezone

from core.config import freeze_config
from core.events import EventType
from core.schemas import (
    AdaptiveReport,
    AgentState,
    AssumptionsDraft,
    BudgetConfig,
    BudgetState,
    CompanyIntake,
    CompanyUnderstanding,
    EvidenceItem,
    FieldKnowledge,
    Hypothesis,
    IndustryContext,
    Opportunity,
    PainPoint,
    ReasoningState,
    Run,
    RunStatus,
    SpawnRequest,
    UserInteractionPoint,
)
from services import trace

_runs: dict[str, Run] = {}

VALID_TRANSITIONS: dict[RunStatus, list[RunStatus]] = {
    # Legacy linear pipeline (still works with orchestration.mode=legacy)
    RunStatus.CREATED: [RunStatus.INTAKE, RunStatus.FAILED],
    RunStatus.INTAKE: [RunStatus.ASSUMPTIONS_DRAFT, RunStatus.GROUNDING, RunStatus.FAILED],
    RunStatus.ASSUMPTIONS_DRAFT: [RunStatus.ASSUMPTIONS_CONFIRMED, RunStatus.FAILED],
    RunStatus.ASSUMPTIONS_CONFIRMED: [RunStatus.REASONING, RunStatus.GROUNDING, RunStatus.FAILED],
    RunStatus.REASONING: [RunStatus.SYNTHESIS, RunStatus.FAILED],
    RunStatus.SYNTHESIS: [RunStatus.REPORT, RunStatus.FAILED],
    RunStatus.REPORT: [RunStatus.PUBLISHED, RunStatus.FAILED],
    # Multi-agent pipeline (with backtracking)
    RunStatus.GROUNDING: [RunStatus.DEEP_RESEARCH, RunStatus.FAILED],
    RunStatus.DEEP_RESEARCH: [RunStatus.HYPOTHESIS_FORMATION, RunStatus.GROUNDING, RunStatus.FAILED],
    RunStatus.HYPOTHESIS_FORMATION: [RunStatus.HYPOTHESIS_TESTING, RunStatus.DEEP_RESEARCH, RunStatus.FAILED],
    RunStatus.HYPOTHESIS_TESTING: [RunStatus.SYNTHESIS, RunStatus.HYPOTHESIS_FORMATION, RunStatus.DEEP_RESEARCH, RunStatus.FAILED],
    RunStatus.REVIEW: [RunStatus.PUBLISHED, RunStatus.HYPOTHESIS_TESTING, RunStatus.DEEP_RESEARCH, RunStatus.FAILED],
}


def create_run(
    company_name: str,
    industry: str,
    config_overrides: dict | None = None,
) -> Run:
    run_id = str(uuid.uuid4())
    config_snapshot = freeze_config(config_overrides)
    budgets = BudgetConfig(**config_snapshot["budgets"])

    run = Run(
        run_id=run_id,
        status=RunStatus.CREATED,
        created_at=datetime.now(timezone.utc),
        config_snapshot=config_snapshot,
        budgets=budgets,
        budget_state=BudgetState(),
    )
    _runs[run_id] = run

    trace.emit(run_id, EventType.RUN_CREATED, {"company_name": company_name, "industry": industry})
    trace.emit(run_id, EventType.CONFIG_SNAPSHOT_SAVED, {"snapshot_keys": list(config_snapshot.keys())})
    return run


def get_run(run_id: str) -> Run | None:
    return _runs.get(run_id)


def update_intake(run_id: str, intake: CompanyIntake) -> Run:
    run = _require_run(run_id)
    run.company_intake = intake
    run.status = RunStatus.INTAKE
    trace.emit(run_id, EventType.COMPANY_INTAKE_SAVED, {"company_name": intake.company_name})
    return run


def transition(run_id: str, new_status: RunStatus) -> Run:
    run = _require_run(run_id)
    allowed = VALID_TRANSITIONS.get(run.status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Invalid transition: {run.status.value} -> {new_status.value}. "
            f"Allowed: {[s.value for s in allowed]}"
        )
    run.status = new_status
    return run


def add_evidence(run_id: str, items: list[EvidenceItem], source_label: str = "unknown") -> Run:
    """Validate and promote evidence through the promotion gate.

    Only promoted (accepted) items are written to run.evidence.
    Canonical source is always EvidenceStore; run.evidence is for API compat.
    """
    from services.memory.store import get_evidence_store
    from services.memory.promotion import PromotionGate
    run = _require_run(run_id)
    gate = PromotionGate(store=get_evidence_store())
    result = gate.promote_batch(run_id, items, source_label=source_label)
    run.evidence.extend(result.accepted_items)
    return run


def get_evidence(run_id: str) -> list[EvidenceItem]:
    """Read evidence from the canonical store."""
    from services.memory.store import get_evidence_store
    return get_evidence_store().get_all(run_id)


def update_reasoning_state(run_id: str, state: ReasoningState) -> Run:
    """Store current reasoning loop state on run."""
    run = _require_run(run_id)
    run.reasoning_state = state
    return run


def update_working_memory(
    run_id: str,
    fields: dict[str, FieldKnowledge],
    hypotheses: list[str] | None = None,
) -> Run:
    """Persist synthesized field knowledge from working memory onto the run.

    Called after reasoning loop completes so downstream agents can read
    the team's synthesized understanding without re-deriving from raw evidence.
    """
    run = _require_run(run_id)
    run.working_memory = fields
    if hypotheses is not None:
        run.hypotheses_legacy = hypotheses
    return run


# --- Multi-agent state updates ---

def update_company_understanding(run_id: str, understanding: CompanyUnderstanding) -> Run:
    run = _require_run(run_id)
    run.company_understanding = understanding
    return run


def update_industry_context(run_id: str, context: IndustryContext) -> Run:
    run = _require_run(run_id)
    run.industry_context = context
    return run


def add_pain_points(run_id: str, pain_points: list[PainPoint]) -> Run:
    run = _require_run(run_id)
    run.pain_points.extend(pain_points)
    return run


def add_hypotheses(run_id: str, hypotheses: list[Hypothesis]) -> Run:
    run = _require_run(run_id)
    run.hypotheses.extend(hypotheses)
    return run


def update_hypothesis(run_id: str, hypothesis_id: str, updates: dict) -> Run:
    run = _require_run(run_id)
    for h in run.hypotheses:
        if h.hypothesis_id == hypothesis_id:
            for k, v in updates.items():
                setattr(h, k, v)
            break
    return run


def add_agent_state(run_id: str, agent_state: AgentState) -> Run:
    run = _require_run(run_id)
    run.agent_states.append(agent_state)
    return run


def update_agent_state(run_id: str, agent_id: str, updates: dict) -> Run:
    run = _require_run(run_id)
    for ag in run.agent_states:
        if ag.agent_id == agent_id:
            for k, v in updates.items():
                setattr(ag, k, v)
            break
    return run


def add_user_interaction(run_id: str, interaction: UserInteractionPoint) -> Run:
    run = _require_run(run_id)
    run.user_interactions.append(interaction)
    return run


def store_adaptive_report(run_id: str, report: AdaptiveReport) -> Run:
    run = _require_run(run_id)
    run.adaptive_report = report
    return run


def update_assumptions(run_id: str, assumptions: AssumptionsDraft) -> Run:
    """Store assumptions draft on run."""
    run = _require_run(run_id)
    run.assumptions = assumptions
    return run


def store_opportunities(run_id: str, opportunities: list[Opportunity]) -> Run:
    """Store synthesized opportunities on the run."""
    from services.memory.opp_store import get_opportunity_store
    run = _require_run(run_id)
    run.opportunities = opportunities
    get_opportunity_store().store(run_id, opportunities)
    return run


def store_report(run_id: str, report: dict) -> Run:
    """Store composed report on the run."""
    from services.memory.report_store import get_report_store
    run = _require_run(run_id)
    run.report = report
    get_report_store().store(run_id, report)
    return run


def _require_run(run_id: str) -> Run:
    run = _runs.get(run_id)
    if run is None:
        raise ValueError(f"Run not found: {run_id}")
    return run
