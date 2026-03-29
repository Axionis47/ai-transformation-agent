"""Multi-agent pipeline orchestrator — pure Python control flow.

Drives: grounding → synthesis → research → synthesis → hypothesis formation
→ hypothesis testing → confidence-driven depth → spawn handling → synthesis.

NOT an LLM agent. The only thing that writes to run_manager (rule #1).
"""
from __future__ import annotations

import asyncio
import logging

from core.events import EventType
from core.schemas import AgentScope, BudgetState, HypothesisStatus, Run, RunStatus
from core import run_manager as rm
from engines.agents.base import BaseResearchAgent
from engines.agents.company_profiler import CompanyProfilerAgent
from engines.agents.industry_analyst import IndustryAnalystAgent
from engines.agents.pain_investigator import PainPointInvestigatorAgent
from engines.agents.hypothesis_former import HypothesisFormerAgent
from engines.context_provider import AgentContextProvider
from engines.hypothesis_tracker import HypothesisTracker
from engines.orchestrator_helpers import (
    generate_report,
    handle_spawns,
    has_budget,
    promote_result,
    synthesize_between_phases,
    test_hypotheses,
)
from engines.phase_synthesis import PhaseSynthesizer
from services.memory.synthesis_store import get_synthesis_store
from services.trace import emit

log = logging.getLogger(__name__)


class Orchestrator:
    """Drives the multi-agent hypothesis pipeline."""

    def __init__(self, config: dict, grounder: object, rag_retriever: object) -> None:
        self._config = config
        self._grounder = grounder
        self._rag = rag_retriever
        self._tracker = HypothesisTracker()
        if grounder is not None:
            self._synthesizer = PhaseSynthesizer(grounder, get_synthesis_store())

        # --- User depth / confidence controls ---
        reasoning = config.get("reasoning", {})
        depth = int(reasoning.get("depth_budget", 5))
        self._confidence_target = float(reasoning.get("confidence_threshold", 0.7))

        scale = depth / 5.0
        self._steps = {
            "company_profiler": max(2, min(12, round(6 * scale))),
            "industry_analyst": max(2, min(8, round(4 * scale))),
            "pain_investigator": max(2, min(12, round(6 * scale))),
            "hypothesis_former": max(2, min(8, round(4 * scale))),
            "hypothesis_tester": max(2, min(8, round(4 * scale))),
        }
        self._max_hypotheses = max(2, min(10, round(5 * scale)))

        self._validate_threshold = self._confidence_target
        self._reject_threshold = self._confidence_target * 0.3

        # Inject thresholds into config for helpers that receive config dict
        self._config["_validate_threshold"] = self._validate_threshold
        self._config["_reject_threshold"] = self._reject_threshold
        self._config["_max_hypotheses"] = self._max_hypotheses

    async def run(self, run_id: str) -> Run:
        """Execute the full pipeline for a run."""
        try:
            await self._run_grounding_phase(run_id)
            await synthesize_between_phases(self._synthesizer, run_id, "grounding")
            await self._run_deep_research_phase(run_id)
            await synthesize_between_phases(self._synthesizer, run_id, "deep_research")
            await self._run_hypothesis_formation_phase(run_id)
            await self._run_hypothesis_testing_phase(run_id)
            await synthesize_between_phases(self._synthesizer, run_id, "hypothesis_testing")
            rm.transition(run_id, RunStatus.SYNTHESIS)
            await self._run_report_phase(run_id)
            return rm.get_run(run_id)  # type: ignore[return-value]
        except Exception as exc:
            log.exception("Pipeline failed for run %s", run_id)
            emit(run_id, EventType.STAGE_FAILED, {"error": str(exc)})
            try:
                rm.transition(run_id, RunStatus.FAILED)
            except ValueError:
                pass
            return rm.get_run(run_id)  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Phase runners
    # ------------------------------------------------------------------
    async def _run_grounding_phase(self, run_id: str) -> None:
        rm.transition(run_id, RunStatus.GROUNDING)
        emit(run_id, EventType.REASONING_LOOP_STARTED, {"phase": "grounding"})

        run = rm.get_run(run_id)
        assert run is not None
        budget = run.budget_state

        profiler = self._create_agent(
            CompanyProfilerAgent, run, AgentScope.COMPANY_PROFILER, budget
        )
        analyst = self._create_agent(
            IndustryAnalystAgent, run, AgentScope.INDUSTRY_ANALYST, budget
        )
        results = await asyncio.gather(
            profiler.run(), analyst.run(), return_exceptions=True
        )
        for r in results:
            if isinstance(r, Exception):
                log.error("Grounding agent failed: %s", r)
                continue
            promote_result(run_id, r)

    async def _run_deep_research_phase(self, run_id: str) -> None:
        rm.transition(run_id, RunStatus.DEEP_RESEARCH)
        emit(run_id, EventType.REASONING_LOOP_STARTED, {"phase": "deep_research"})

        run = rm.get_run(run_id)
        assert run is not None
        investigator = self._create_agent(
            PainPointInvestigatorAgent, run,
            AgentScope.PAIN_INVESTIGATOR, run.budget_state,
        )
        result = await investigator.run()
        promote_result(run_id, result)

    async def _run_hypothesis_formation_phase(self, run_id: str) -> None:
        rm.transition(run_id, RunStatus.HYPOTHESIS_FORMATION)
        emit(run_id, EventType.REASONING_LOOP_STARTED, {"phase": "hypothesis_formation"})

        run = rm.get_run(run_id)
        assert run is not None
        former = self._create_agent(
            HypothesisFormerAgent, run,
            AgentScope.HYPOTHESIS_FORMER, run.budget_state,
        )
        result = await former.run()
        promote_result(run_id, result)
        for h in result.hypotheses:
            if not self._tracker.get(h.hypothesis_id):
                self._tracker._hypotheses[h.hypothesis_id] = h

    async def _run_hypothesis_testing_phase(self, run_id: str) -> None:
        rm.transition(run_id, RunStatus.HYPOTHESIS_TESTING)
        emit(run_id, EventType.REASONING_LOOP_STARTED, {"phase": "hypothesis_testing"})

        run = rm.get_run(run_id)
        assert run is not None
        args = (self._tracker, self._config, self._grounder, self._rag)

        # First pass: test all hypotheses in parallel
        await test_hypotheses(run_id, run.hypotheses, run.budget_state, *args)

        # Confidence-driven depth: retest low-confidence hypotheses
        if has_budget(run.budget_state, self._config):
            low = self._tracker.get_low_confidence(self._validate_threshold)
            if low:
                emit(run_id, EventType.REASONING_LOOP_STARTED, {"phase": "confidence_depth"})
                await test_hypotheses(run_id, low, run.budget_state, *args)

        # Handle spawn requests
        run = rm.get_run(run_id)
        assert run is not None
        if run.spawn_requests and has_budget(run.budget_state, self._config):
            await handle_spawns(run_id, run.budget_state, *args)

        # Finalize: force-validate/reject hypotheses still stuck in "testing"
        for h in self._tracker.get_all():
            if h.status == HypothesisStatus.TESTING:
                if h.confidence >= self._validate_threshold:
                    self._tracker.validate(h.hypothesis_id, f"Confidence {h.confidence:.0%} meets threshold after testing")
                    emit(run_id, EventType.HYPOTHESIS_VALIDATED, {"hypothesis_id": h.hypothesis_id, "confidence": h.confidence})
                elif h.confidence < self._reject_threshold:
                    self._tracker.reject(h.hypothesis_id, f"Confidence {h.confidence:.0%} below rejection threshold")
                    emit(run_id, EventType.HYPOTHESIS_REJECTED, {"hypothesis_id": h.hypothesis_id, "confidence": h.confidence})
                else:
                    # Between thresholds — validate with conditions
                    self._tracker.validate_with_conditions(h.hypothesis_id, f"Moderate confidence {h.confidence:.0%}", ["Requires further validation"])
                    emit(run_id, EventType.HYPOTHESIS_VALIDATED, {"hypothesis_id": h.hypothesis_id, "confidence": h.confidence})
        # Sync finalized hypotheses to run state
        rm.add_hypotheses(run_id, self._tracker.get_all())

    async def _run_report_phase(self, run_id: str) -> None:
        rm.transition(run_id, RunStatus.REPORT)
        emit(run_id, EventType.REASONING_LOOP_STARTED, {"phase": "report"})
        run = rm.get_run(run_id)
        assert run is not None
        report_result = await generate_report(
            run_id, run, self._tracker, self._config,
            self._grounder, self._rag,
        )
        if report_result and report_result.adaptive_report:
            rm.store_adaptive_report(run_id, report_result.adaptive_report)
            promote_result(run_id, report_result)
        rm.transition(run_id, RunStatus.REVIEW)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------
    def _create_agent(
        self, cls: type, run: Run, scope: AgentScope, budget: BudgetState
    ) -> BaseResearchAgent:
        agent_type = cls.AGENT_TYPE
        return cls(
            config=self._config,
            grounder=self._grounder,
            rag_retriever=self._rag,
            context_provider=AgentContextProvider(run, scope),
            budget_state=budget,
            run_id=run.run_id,
            max_steps=self._steps.get(agent_type),
        )
