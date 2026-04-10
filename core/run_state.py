"""Domain state updates for runs — evidence, hypotheses, agent tracking, reports.

Split from run_manager.py to separate CRUD/transitions from domain mutations.
All functions follow the pattern: require_run() -> mutate -> persist().
"""

from __future__ import annotations

from core.run_manager import _persist, _require_run
from core.schemas import (
    AdaptiveReport,
    AgentState,
    AssumptionsDraft,
    CompanyUnderstanding,
    EvidenceItem,
    FieldKnowledge,
    Hypothesis,
    IndustryContext,
    Opportunity,
    PainPoint,
    ReasoningState,
    Run,
    UserInteractionPoint,
)


def add_evidence(
    run_id: str,
    items: list[EvidenceItem],
    source_label: str = "unknown",
    phase: str = "grounding",
) -> Run:
    from services.memory.promotion import PromotionGate
    from services.memory.store import get_evidence_store

    run = _require_run(run_id)
    gate = PromotionGate(store=get_evidence_store())
    result = gate.promote_batch(run_id, items, source_label=source_label, phase=phase)
    run.evidence.extend(result.accepted_items)
    return _persist(run)


def get_evidence(run_id: str) -> list[EvidenceItem]:
    from services.memory.store import get_evidence_store

    return get_evidence_store().get_all(run_id)


def update_reasoning_state(run_id: str, state: ReasoningState) -> Run:
    run = _require_run(run_id)
    run.reasoning_state = state
    return _persist(run)


def update_working_memory(
    run_id: str,
    fields: dict[str, FieldKnowledge],
    hypotheses: list[str] | None = None,
) -> Run:
    run = _require_run(run_id)
    run.working_memory = fields
    if hypotheses is not None:
        run.hypotheses_legacy = hypotheses
    return _persist(run)


# --- Multi-agent state updates ---


def update_company_understanding(run_id: str, understanding: CompanyUnderstanding) -> Run:
    run = _require_run(run_id)
    run.company_understanding = understanding
    return _persist(run)


def update_industry_context(run_id: str, context: IndustryContext) -> Run:
    run = _require_run(run_id)
    run.industry_context = context
    return _persist(run)


def add_pain_points(run_id: str, pain_points: list[PainPoint]) -> Run:
    run = _require_run(run_id)
    run.pain_points.extend(pain_points)
    return _persist(run)


def add_hypotheses(run_id: str, hypotheses: list[Hypothesis]) -> Run:
    run = _require_run(run_id)
    existing_ids = {h.hypothesis_id for h in run.hypotheses}
    for h in hypotheses:
        if h.hypothesis_id in existing_ids:
            for i, eh in enumerate(run.hypotheses):
                if eh.hypothesis_id == h.hypothesis_id:
                    run.hypotheses[i] = h
                    break
        else:
            run.hypotheses.append(h)
            existing_ids.add(h.hypothesis_id)
    return _persist(run)


def update_hypothesis(run_id: str, hypothesis_id: str, updates: dict) -> Run:
    run = _require_run(run_id)
    for h in run.hypotheses:
        if h.hypothesis_id == hypothesis_id:
            for k, v in updates.items():
                setattr(h, k, v)
            break
    return _persist(run)


def add_agent_state(run_id: str, agent_state: AgentState) -> Run:
    run = _require_run(run_id)
    run.agent_states.append(agent_state)
    return _persist(run)


def update_agent_state(run_id: str, agent_id: str, updates: dict) -> Run:
    run = _require_run(run_id)
    for ag in run.agent_states:
        if ag.agent_id == agent_id:
            for k, v in updates.items():
                setattr(ag, k, v)
            break
    return _persist(run)


def add_user_interaction(run_id: str, interaction: UserInteractionPoint) -> Run:
    run = _require_run(run_id)
    run.user_interactions.append(interaction)
    return _persist(run)


def store_adaptive_report(run_id: str, report: AdaptiveReport) -> Run:
    run = _require_run(run_id)
    run.adaptive_report = report
    return _persist(run)


def update_assumptions(run_id: str, assumptions: AssumptionsDraft) -> Run:
    run = _require_run(run_id)
    run.assumptions = assumptions
    return _persist(run)


def store_opportunities(run_id: str, opportunities: list[Opportunity]) -> Run:
    from services.memory.opp_store import get_opportunity_store

    run = _require_run(run_id)
    run.opportunities = opportunities
    get_opportunity_store().store(run_id, opportunities)
    return _persist(run)


def store_report(run_id: str, report: dict) -> Run:
    from services.memory.report_store import get_report_store

    run = _require_run(run_id)
    run.report = report
    get_report_store().store(run_id, report)
    return _persist(run)
