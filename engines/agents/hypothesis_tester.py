"""HypothesisTester agent — stress-tests a single hypothesis.

One instance per hypothesis, runs in parallel. Uses BOTH tools:
GROUND (search for counter-evidence) and RAG (find anti-patterns).
Tracks running confidence and validates/rejects based on thresholds.
"""
from __future__ import annotations

from core.json_parser import extract_json
from core.schemas import (
    AgentResult,
    DerivedInsight,
    Hypothesis,
    SpawnRequest,
    TestResult,
)
from engines.agents.base import AgentThought, BaseResearchAgent
from engines.hypothesis_tracker import HypothesisTracker


class HypothesisTesterAgent(BaseResearchAgent):
    """Stress-tests one hypothesis via disconfirmation search."""

    AGENT_TYPE = "hypothesis_tester"
    PROMPT_NAME = "agent_hypothesis_tester"
    MAX_STEPS = 6

    def __init__(
        self, *, hypothesis: Hypothesis, tracker: HypothesisTracker, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        if self._max_steps_override is not None:
            self.MAX_STEPS = self._max_steps_override
        else:
            agent_cfg = self._config.get("agents", {}).get("hypothesis_tester", {})
            self.MAX_STEPS = int(agent_cfg.get("max_steps", 6))
        self._hypothesis = hypothesis
        self._tracker = tracker
        # Register hypothesis in tracker if not already there
        if not self._tracker.get(hypothesis.hypothesis_id):
            self._tracker._hypotheses[hypothesis.hypothesis_id] = hypothesis
        self._hypothesis.tested_by_agent = self._agent_id
        self._confidence = hypothesis.confidence
        self._validate_threshold = float(self._config.get("_validate_threshold", 0.5))
        self._reject_threshold = float(self._config.get("_reject_threshold", 0.2))
        self._past_queries: list[str] = []
        self._spawn_requests: list[SpawnRequest] = []
        self._test_count = 0
        self._early_stop = False

    # ------------------------------------------------------------------
    # ReAct: THINK
    # ------------------------------------------------------------------
    async def _think(self, context: str) -> AgentThought:
        if self._early_stop:
            return AgentThought(action="STOP", reasoning="early stop triggered")

        intake = self._ctx.get_intake() if self._ctx else None
        company = intake.company_name if intake else "unknown"
        industry = intake.industry if intake else "unknown"

        # Pull evidence focused on the hypothesis's target process
        focused = self._ctx.query_evidence(
            process_area=self._hypothesis.target_process, top_k=10
        ) if self._ctx else []
        if focused:
            ev_lines = [f"  - {e.title}: {e.snippet[:100]}" for e in focused]
            context += "\n\nFOCUSED EVIDENCE (target process):\n" + "\n".join(ev_lines)

        # Pull confirmed findings from prior phases so tester doesn't re-research them
        insights = self._ctx.get_derived_insights() if self._ctx else []
        if insights:
            context += "\n\nCONFIRMED FINDINGS (do NOT re-search, build on these):\n"
            context += "\n".join(f"  - {i.statement} [{i.confidence:.0%}]" for i in insights[:8])

        pain_points = self._ctx.get_pain_points() if self._ctx else []
        if pain_points:
            context += "\n\nKNOWN PAIN POINTS:\n"
            context += "\n".join(f"  - [{p.severity.upper()}] {p.description}" for p in pain_points[:5])

        prompt = self._system_prompt.format(
            hypothesis_statement=self._hypothesis.statement,
            hypothesis_category=self._hypothesis.category,
            hypothesis_target_process=self._hypothesis.target_process,
            hypothesis_evidence_for=", ".join(self._hypothesis.evidence_for[:5]),
            company_name=company,
            industry=industry,
            context_briefing=context,
            ground_remaining=self._ground_remaining(),
            rag_remaining=self._rag_remaining(),
        )

        if self._past_queries:
            prompt += "\n\nPrevious queries (do NOT repeat):\n"
            prompt += "\n".join(f"- {q}" for q in self._past_queries)
        prompt += f"\n\nCurrent confidence: {self._confidence:.2f}"
        prompt += f"\nTests run so far: {self._test_count}"

        raw = self._grounder.reason(prompt, self._run_id)
        if not raw:
            return AgentThought(action="STOP", reasoning="LLM returned empty")

        parsed = extract_json(raw)
        if not parsed or "action" not in parsed:
            return AgentThought(action="STOP", reasoning="unparseable response")

        action = parsed.get("action", "STOP").upper()
        query = parsed.get("query", "")
        reasoning = parsed.get("reasoning", "")

        # Record test result if present
        self._process_test_result(parsed)
        self._process_spawn_request(parsed)

        # Check confidence thresholds and LLM recommendation
        recommendation = parsed.get("recommendation", "continue")
        conditions = parsed.get("conditions", [])
        if not isinstance(conditions, list):
            conditions = []

        if self._confidence < self._reject_threshold:
            self._tracker.reject(
                self._hypothesis.hypothesis_id,
                f"Confidence dropped to {self._confidence:.2f} after {self._test_count} tests",
            )
            self._early_stop = True
            return AgentThought(action="STOP", reasoning=f"confidence below {self._reject_threshold} — rejected")

        if recommendation == "validate_with_conditions" and conditions:
            self._tracker.validate_with_conditions(
                self._hypothesis.hypothesis_id,
                f"Conditionally validated at {self._confidence:.2f} after {self._test_count} tests",
                conditions,
            )
            self._early_stop = True
            return AgentThought(
                action="STOP",
                reasoning=f"conditionally validated — requires: {', '.join(conditions)}",
            )

        if recommendation == "validate" and self._confidence > self._validate_threshold and self._test_count >= 3:
            self._tracker.validate(
                self._hypothesis.hypothesis_id,
                f"Confidence held at {self._confidence:.2f} after {self._test_count} tests",
            )
            self._early_stop = True
            return AgentThought(action="STOP", reasoning=f"confidence above {self._validate_threshold} after 3+ tests — validated")

        # Duplicate query guard
        if action in ("GROUND", "RAG") and query:
            if query in self._past_queries:
                return AgentThought(action="STOP", reasoning="duplicate query — stopping")
            self._past_queries.append(query)

        if action not in ("GROUND", "RAG", "STOP"):
            action = "STOP"

        return AgentThought(action=action, query=query, reasoning=reasoning)

    # ------------------------------------------------------------------
    # ReAct: OBSERVE — tag evidence with hypothesis dimension
    # ------------------------------------------------------------------
    def _observe(self, observation: str) -> None:
        for ev in self._evidence[self._prev_evidence_count:]:
            ev.dimension = "hypothesis_test"
            ev.process_area = self._hypothesis.target_process
            ev.produced_by = self._agent_id

    # ------------------------------------------------------------------
    # ReAct: helpers
    # ------------------------------------------------------------------
    def _process_test_result(self, parsed: dict) -> None:
        raw_tr = parsed.get("test_result")
        if not isinstance(raw_tr, dict) or not raw_tr.get("finding"):
            return
        ev_ids = raw_tr.get("evidence_ids", [])
        if not isinstance(ev_ids, list):
            ev_ids = []
        impact = float(raw_tr.get("impact_on_confidence", 0))
        impact = max(-0.20, min(0.20, impact))  # symmetric clamp

        tr = TestResult(
            test_type=raw_tr.get("test_type", "evidence_search"),
            finding=raw_tr["finding"],
            impact_on_confidence=impact,
            evidence_ids=ev_ids,
        )
        narrative = f"Test {self._test_count + 1}: {tr.finding}"
        self._tracker.record_test(self._hypothesis.hypothesis_id, tr, narrative)
        self._confidence = self._hypothesis.confidence
        self._test_count += 1

    def _process_spawn_request(self, parsed: dict) -> None:
        raw_sr = parsed.get("spawn_request")
        if not isinstance(raw_sr, dict) or not raw_sr.get("suggested_hypothesis"):
            return
        self._spawn_requests.append(SpawnRequest(
            requesting_agent=self._agent_id,
            reason=raw_sr.get("reason", "Discovered during testing"),
            suggested_hypothesis=raw_sr["suggested_hypothesis"],
            priority="medium",
        ))

    # ------------------------------------------------------------------
    # Result builder
    # ------------------------------------------------------------------
    def _build_result(self, error: str | None = None) -> AgentResult:
        insights = self._build_insights()
        return AgentResult(
            agent_id=self._agent_id,
            agent_type=self.AGENT_TYPE,
            success=error is None,
            evidence_items=self._evidence,
            derived_insights=insights,
            summary=self._build_summary(),
            error=error,
            hypotheses=[self._hypothesis],
            spawn_requests=self._spawn_requests,
        )

    def _build_insights(self) -> list[DerivedInsight]:
        h = self._hypothesis
        return [DerivedInsight(
            insight_id=f"ins-ht-{h.hypothesis_id}",
            phase="hypothesis_testing",
            statement=f"Tested: {h.statement} — {h.status.value} ({h.confidence:.0%})",
            supporting_evidence_ids=h.evidence_for[:5],
            confidence=h.confidence,
            produced_by_agent=self._agent_id,
        )]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _ground_remaining(self) -> int:
        cap = int(self._config.get("budgets", {}).get("external_search_query_budget", 5))
        return max(0, cap - self._budget.external_search_queries_used)

    def _rag_remaining(self) -> int:
        cap = int(self._config.get("budgets", {}).get("rag_query_budget", 8))
        return max(0, cap - self._budget.rag_queries_used)

    def _build_summary(self) -> str:
        h = self._hypothesis
        return (
            f"hypothesis_tester: {self._steps_taken} steps, "
            f"{self._test_count} tests, "
            f"{h.status.value} ({h.confidence:.0%})"
        )
