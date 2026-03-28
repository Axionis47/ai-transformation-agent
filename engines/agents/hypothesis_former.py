"""HypothesisFormer agent — reasons from evidence to form AI hypotheses.

Runs AFTER CompanyProfiler, IndustryAnalyst, and PainInvestigator.
Uses RAG only (analogous past engagements). NO grounding.
Returns typed AgentResult with hypotheses registered via HypothesisTracker.
"""
from __future__ import annotations

from core.json_parser import extract_json
from core.schemas import AgentResult, DerivedInsight, Hypothesis
from engines.agents.base import AgentThought, BaseResearchAgent
from engines.hypothesis_tracker import HypothesisTracker


class HypothesisFormerAgent(BaseResearchAgent):
    """Forms AI opportunity hypotheses from accumulated evidence + RAG."""

    AGENT_TYPE = "hypothesis_former"
    PROMPT_NAME = "agent_hypothesis_former"
    MAX_STEPS = 5

    def __init__(self, **kwargs) -> None:  # type: ignore[override]
        super().__init__(**kwargs)
        if self._max_steps_override is not None:
            self.MAX_STEPS = self._max_steps_override
        else:
            agent_cfg = self._config.get("agents", {}).get("hypothesis_former", {})
            self.MAX_STEPS = int(agent_cfg.get("max_steps", 5))
        self._past_queries: list[str] = []
        self._raw_hypotheses: list[dict] = []
        self._tracker = HypothesisTracker()

    # ------------------------------------------------------------------
    # ReAct: THINK
    # ------------------------------------------------------------------
    async def _think(self, context: str) -> AgentThought:
        intake = self._ctx.get_intake() if self._ctx else None
        company = intake.company_name if intake else "unknown"
        industry = intake.industry if intake else "unknown"

        # Pull structured insights and pain points from prior phases
        insights = self._ctx.get_derived_insights() if self._ctx else []
        pain_points = self._ctx.get_pain_points() if self._ctx else []

        # Pull focused evidence by dimension for structured input
        pain_ev = self._ctx.query_evidence(dimension="pain_point", top_k=5) if self._ctx else []
        tech_ev = self._ctx.query_evidence(dimension="technology", top_k=3) if self._ctx else []
        if pain_ev or tech_ev:
            ev_lines = [f"  - {e.title}: {e.snippet[:100]}" for e in pain_ev + tech_ev]
            context += "\n\nFOCUSED EVIDENCE (pain+tech):\n" + "\n".join(ev_lines)

        structured_inputs = ""
        if insights:
            structured_inputs += (
                "\nSTRUCTURED INSIGHTS (from prior agents):\n"
            )
            structured_inputs += "\n".join(
                f"- [{i.phase}] {i.statement} [{i.confidence:.0%}]"
                for i in insights
            )
        if pain_points:
            structured_inputs += "\nIDENTIFIED PAIN POINTS:\n"
            structured_inputs += "\n".join(
                f"- [{pp.severity.upper()}] {pp.description}"
                f" (process: {pp.affected_process})"
                for pp in pain_points
            )

        prompt = self._system_prompt.format(
            company_name=company,
            industry=industry,
            context_briefing=context,
            rag_remaining=self._rag_remaining(),
        )

        # Inject structured inputs after context briefing
        if structured_inputs:
            prompt += structured_inputs

        if self._past_queries:
            prompt += "\n\nPrevious RAG queries (do NOT repeat):\n"
            prompt += "\n".join(f"- {q}" for q in self._past_queries)

        if self._evidence:
            prompt += f"\n\nRAG evidence collected: {len(self._evidence)} items."

        raw = self._grounder.reason(prompt, self._run_id)
        if not raw:
            return AgentThought(action="STOP", reasoning="LLM returned empty")

        parsed = extract_json(raw)
        if not parsed or "action" not in parsed:
            return AgentThought(action="STOP", reasoning="unparseable response")

        action = parsed.get("action", "STOP").upper()
        query = parsed.get("query", "")
        reasoning = parsed.get("reasoning", "")

        # Keep latest hypotheses list from LLM
        hyp_list = parsed.get("hypotheses", [])
        if isinstance(hyp_list, list) and hyp_list:
            self._raw_hypotheses = hyp_list

        # Only allow RAG or STOP — ignore GROUND
        if action == "GROUND":
            action = "RAG"

        if action == "RAG" and query:
            if query in self._past_queries:
                return AgentThought(
                    action="STOP", reasoning="duplicate query — stopping"
                )
            self._past_queries.append(query)

        if action not in ("RAG", "STOP"):
            action = "STOP"

        return AgentThought(
            action=action, query=query, reasoning=reasoning
        )

    # ------------------------------------------------------------------
    # ReAct: ACT — only RAG, override to block GROUND
    # ------------------------------------------------------------------
    async def _act(self, thought: AgentThought) -> str:
        if thought.action == "RAG" and self._rag:
            self._budget.total_tool_calls_used += 1
            rag_result = self._rag.query(
                thought.query, self._run_id, self._budget
            )
            if rag_result.budget_exhausted:
                return "RAG BUDGET EXHAUSTED"
            self._evidence.extend(rag_result.results)
            snippets = [
                f"- {r.source_ref}: {r.snippet[:100]}"
                for r in rag_result.results[:3]
            ]
            return (
                f"RAG returned {len(rag_result.results)} results:\n"
                + "\n".join(snippets)
            )
        return f"Unknown action: {thought.action}"

    # ------------------------------------------------------------------
    # Result builder
    # ------------------------------------------------------------------
    def _build_result(self, error: str | None = None) -> AgentResult:
        hypotheses = self._register_hypotheses()
        insights = self._build_insights(hypotheses)

        return AgentResult(
            agent_id=self._agent_id,
            agent_type=self.AGENT_TYPE,
            success=error is None,
            evidence_items=self._evidence,
            derived_insights=insights,
            summary=self._build_summary(),
            error=error,
            hypotheses=hypotheses,
        )

    def _register_hypotheses(self) -> list[Hypothesis]:
        """Register raw LLM hypotheses with HypothesisTracker."""
        max_h = int(self._config.get("_max_hypotheses", 7))
        evidence_ids = [e.evidence_id for e in self._evidence]
        for raw in self._raw_hypotheses[:max_h]:
            if not isinstance(raw, dict) or not raw.get("statement"):
                continue
            raw_evidence = raw.get("evidence_for", [])
            # Use LLM-cited evidence if valid, else fallback to collected
            ev_for = (
                raw_evidence
                if isinstance(raw_evidence, list) and raw_evidence
                else evidence_ids[:3]
            )
            self._tracker.form(
                statement=raw["statement"],
                category=raw.get("category", "automation"),
                target_process=raw.get("target_process", "general"),
                evidence_for=ev_for,
                reason=raw.get("formed_because", "Formed from evidence"),
                agent_id=self._agent_id,
            )
        # Update confidence based on evidence count
        for h in self._tracker.get_all():
            h.confidence = self._compute_confidence(h)
        return self._tracker.get_all()

    def _build_insights(self, hypotheses: list[Hypothesis]) -> list[DerivedInsight]:
        insights: list[DerivedInsight] = []
        for h in hypotheses:
            insights.append(DerivedInsight(
                insight_id=f"ins-hf-{h.hypothesis_id}",
                phase="hypothesis_formation",
                statement=f"Hypothesis: {h.statement}",
                supporting_evidence_ids=h.evidence_for[:5],
                confidence=h.confidence,
                produced_by_agent=self._agent_id,
            ))
        return insights

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _rag_remaining(self) -> int:
        budget_cfg = self._config.get("budgets", {})
        cap = int(budget_cfg.get("rag_query_budget", 8))
        return max(0, cap - self._budget.rag_queries_used)

    def _compute_confidence(self, h: Hypothesis) -> float:
        base = 0.3
        ev_count = min(len(h.evidence_for), 6)
        ev_boost = ev_count * 0.08
        return round(min(base + ev_boost, 0.85), 2)

    def _build_summary(self) -> str:
        n = len(self._tracker.get_all())
        return (
            f"hypothesis_former: {self._steps_taken} steps, "
            f"{len(self._evidence)} evidence, "
            f"{n} hypotheses formed"
        )
