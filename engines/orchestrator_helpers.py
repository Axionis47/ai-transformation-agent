"""Helper functions for the orchestrator — result promotion and synthesis.

Split from orchestrator.py to respect the 200-line limit.
"""

from __future__ import annotations

import logging

from core import run_manager as rm
from core.events import EventType
from core.schemas import (
    AgentResult,
    AgentScope,
    AgentState,
    BudgetState,
    ReportFeedback,
    Run,
)
from engines.agents.hypothesis_tester import HypothesisTesterAgent
from engines.agents.report_synthesizer import ReportSynthesizerAgent
from engines.context_provider import AgentContextProvider
from engines.hypothesis_tracker import HypothesisTracker
from services.memory.synthesis_store import get_synthesis_store
from services.trace import emit

log = logging.getLogger(__name__)


_AGENT_TO_PHASE = {
    "company_profiler": "grounding",
    "industry_analyst": "grounding",
    "pain_investigator": "deep_research",
    "hypothesis_former": "deep_research",
    "hypothesis_tester": "hypothesis_testing",
    "report_synthesizer": "hypothesis_testing",
}


def promote_result(run_id: str, result: AgentResult) -> None:
    """Write agent output into run state via run_manager."""
    rm.add_agent_state(run_id, _result_to_state(result))
    phase = _AGENT_TO_PHASE.get(result.agent_type, "grounding")
    if result.evidence_items:
        rm.add_evidence(run_id, result.evidence_items, source_label=result.agent_type, phase=phase)
    if result.derived_insights:
        get_synthesis_store().save_insights(run_id, result.derived_insights)
    if result.company_understanding:
        rm.update_company_understanding(run_id, result.company_understanding)
    if result.industry_context:
        rm.update_industry_context(run_id, result.industry_context)
    if result.pain_points:
        rm.add_pain_points(run_id, result.pain_points)
    if result.hypotheses:
        rm.add_hypotheses(run_id, result.hypotheses)
    if result.spawn_requests:
        run = rm.get_run(run_id)
        assert run is not None
        run.spawn_requests.extend(result.spawn_requests)


async def synthesize_between_phases(synthesizer: object, run_id: str, phase: str) -> None:
    """Call PhaseSynthesizer between pipeline phases."""
    run = rm.get_run(run_id)
    assert run is not None
    store = get_synthesis_store()
    if phase == "grounding":
        await synthesizer.synthesize_grounding(  # type: ignore[attr-defined]
            run_id, run.company_understanding, run.industry_context, run.evidence
        )
    elif phase == "deep_research":
        briefing = store.get_phase_briefing(run_id, "grounding") or ""
        insights = store.get_insights(run_id)
        await synthesizer.synthesize_research(  # type: ignore[attr-defined]
            run_id, run.pain_points, briefing, run.evidence, insights
        )
    elif phase == "hypothesis_testing":
        insights = store.get_insights(run_id)
        await synthesizer.synthesize_testing(  # type: ignore[attr-defined]
            run_id, run.hypotheses, insights
        )


async def test_hypotheses(
    run_id: str,
    hypotheses: list,
    budget: BudgetState,
    tracker: HypothesisTracker,
    config: dict,
    grounder: object,
    rag: object,
) -> None:
    """Run parallel HypothesisTesters for a list of hypotheses."""
    import asyncio

    run = rm.get_run(run_id)
    assert run is not None
    tasks = []
    for h in hypotheses:
        tester = HypothesisTesterAgent(
            hypothesis=h,
            tracker=tracker,
            config=config,
            grounder=grounder,
            rag_retriever=rag,
            context_provider=AgentContextProvider(run, AgentScope.HYPOTHESIS_TESTER),
            budget_state=budget,
            run_id=run_id,
        )
        tasks.append(tester.run())
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, Exception):
            log.error("Tester failed: %s", r)
            continue
        promote_result(run_id, r)


async def handle_spawns(
    run_id: str,
    budget: BudgetState,
    tracker: HypothesisTracker,
    config: dict,
    grounder: object,
    rag: object,
) -> None:
    """Form and test hypotheses from spawn requests."""
    run = rm.get_run(run_id)
    assert run is not None
    existing_ids = {h.hypothesis_id for h in run.hypotheses}
    for sr in run.spawn_requests:
        emit(run_id, EventType.SPAWN_REQUESTED, {"hypothesis": sr.suggested_hypothesis})
        h = tracker.form(
            statement=sr.suggested_hypothesis,
            category="automation",
            target_process="general",
            evidence_for=[],
            reason=sr.reason,
            agent_id=sr.requesting_agent,
        )
        rm.add_hypotheses(run_id, [h])
    spawned = [h for h in tracker.get_all() if h.hypothesis_id not in existing_ids]
    if spawned and has_budget(budget, config):
        await test_hypotheses(run_id, spawned, budget, tracker, config, grounder, rag)


async def generate_report(
    run_id: str,
    run: Run,
    tracker: HypothesisTracker,
    config: dict,
    grounder: object,
    rag: object,
    feedback: list[ReportFeedback] | None = None,
) -> AgentResult | None:
    """Run ReportSynthesizerAgent to produce the AdaptiveReport."""
    ctx = AgentContextProvider(run, AgentScope.REPORT_SYNTHESIZER)
    previous = run.adaptive_report if feedback else None
    agent = ReportSynthesizerAgent(
        hypotheses=run.hypotheses,
        tracker=tracker,
        feedback=feedback,
        previous_report=previous,
        config=config,
        grounder=grounder,
        rag_retriever=rag,
        context_provider=ctx,
        budget_state=run.budget_state,
        run_id=run_id,
    )
    try:
        result = await agent.run()
        return result
    except Exception as exc:
        log.error("ReportSynthesizer failed: %s", exc)
        return None


def has_budget(budget: BudgetState, config: dict) -> bool:
    """Check if there is remaining budget for more tool calls."""
    budgets = config.get("budgets", {})
    search_cap = int(budgets.get("external_search_query_budget", 25))
    rag_cap = int(budgets.get("rag_query_budget", 15))
    return budget.external_search_queries_used < search_cap or budget.rag_queries_used < rag_cap


def _result_to_state(result: AgentResult) -> AgentState:
    return AgentState(
        agent_id=result.agent_id,
        agent_type=result.agent_type,
        status="completed" if result.success else "failed",
        tool_calls_made=0,
        evidence_produced=[e.evidence_id for e in result.evidence_items],
        summary=result.summary,
    )
