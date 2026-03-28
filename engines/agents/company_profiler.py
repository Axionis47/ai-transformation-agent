"""CompanyProfiler agent — builds a factual CompanyUnderstanding.

Runs a ReAct loop: THINK (ask LLM what to search) → ACT (ground via
Google Search) → OBSERVE (accumulate evidence) → repeat until confident
or budget exhausted. Returns typed AgentResult with CompanyUnderstanding.
"""
from __future__ import annotations

import uuid

from core.json_parser import extract_json
from core.schemas import AgentResult, CompanyUnderstanding, DerivedInsight
from engines.agents.base import AgentThought, BaseResearchAgent

_DIMENSIONS = [
    "what_they_do",
    "how_they_make_money",
    "size_and_scale",
    "technology_landscape",
    "organizational_structure",
]

_DIM_TO_TAG = {
    "what_they_do": "operations",
    "how_they_make_money": "revenue",
    "size_and_scale": "scale",
    "technology_landscape": "technology",
    "organizational_structure": "organization",
}


class CompanyProfilerAgent(BaseResearchAgent):
    """Profiles a company across five dimensions using grounded search."""

    AGENT_TYPE = "company_profiler"
    PROMPT_NAME = "agent_company_profiler"

    def __init__(self, **kwargs) -> None:  # type: ignore[override]
        super().__init__(**kwargs)
        agent_cfg = self._config.get("agents", {}).get("company_profiler", {})
        self.MAX_STEPS = int(agent_cfg.get("max_steps", 8))
        self._past_queries: list[str] = []
        self._assessment: dict[str, str] = {d: "unknown" for d in _DIMENSIONS}
        self._current_dimension: str = "operations"

    # ------------------------------------------------------------------
    # ReAct: THINK
    # ------------------------------------------------------------------
    async def _think(self, context: str) -> AgentThought:
        intake = self._ctx.get_intake() if self._ctx else None
        company = intake.company_name if intake else "unknown"
        industry = intake.industry if intake else "unknown"

        remaining = self._ground_remaining()
        prompt = self._system_prompt.format(
            company_name=company,
            industry=industry,
            context_briefing=context,
            ground_remaining=remaining,
        )

        if self._past_queries:
            prompt += "\n\nPrevious queries (do NOT repeat):\n"
            prompt += "\n".join(f"- {q}" for q in self._past_queries)

        if self._evidence:
            prompt += f"\n\nEvidence collected so far: {len(self._evidence)} items."

        raw = self._grounder.reason(prompt, self._run_id)
        if not raw:
            return AgentThought(action="STOP", reasoning="LLM returned empty")

        parsed = extract_json(raw)
        if not parsed or "action" not in parsed:
            return AgentThought(action="STOP", reasoning="unparseable response")

        action = parsed.get("action", "STOP").upper()
        query = parsed.get("query", "")
        reasoning = parsed.get("reasoning", "")

        assessment = parsed.get("current_assessment", {})
        if isinstance(assessment, dict):
            for dim in _DIMENSIONS:
                val = assessment.get(dim)
                if val and val.lower() != "unknown":
                    self._assessment[dim] = val
                    self._current_dimension = _DIM_TO_TAG.get(dim, "operations")

        if action == "GROUND" and query:
            if query in self._past_queries:
                return AgentThought(
                    action="STOP", reasoning="duplicate query — stopping"
                )
            self._past_queries.append(query)

        return AgentThought(
            action=action, query=query, reasoning=reasoning
        )

    # ------------------------------------------------------------------
    # ReAct: OBSERVE — tag new evidence with current dimension
    # ------------------------------------------------------------------
    def _observe(self, observation: str) -> None:
        for ev in self._evidence[self._prev_evidence_count:]:
            ev.dimension = self._current_dimension or "operations"
            ev.produced_by = self._agent_id

    # ------------------------------------------------------------------
    # Result builder
    # ------------------------------------------------------------------
    def _build_result(self, error: str | None = None) -> AgentResult:
        confidence = self._compute_confidence()
        intake = self._ctx.get_intake() if self._ctx else None

        cu = CompanyUnderstanding(
            company_name=intake.company_name if intake else "unknown",
            what_they_do=self._assessment.get("what_they_do", "unknown"),
            how_they_make_money=self._assessment.get("how_they_make_money", "unknown"),
            size_and_scale=self._assessment.get("size_and_scale", "unknown"),
            technology_landscape=self._assessment.get("technology_landscape", "unknown"),
            organizational_structure=self._assessment.get("organizational_structure", "unknown"),
            confidence=confidence,
            evidence_ids=[e.evidence_id for e in self._evidence],
        )

        return AgentResult(
            agent_id=self._agent_id,
            agent_type=self.AGENT_TYPE,
            success=error is None,
            evidence_items=self._evidence,
            derived_insights=self._build_derived_insights(),
            summary=self._build_summary(),
            error=error,
            company_understanding=cu,
        )

    def _build_derived_insights(self) -> list[DerivedInsight]:
        insights: list[DerivedInsight] = []
        for dim in _DIMENSIONS:
            val = self._assessment.get(dim, "unknown")
            if val.lower() != "unknown":
                insights.append(DerivedInsight(
                    insight_id=f"ins-{uuid.uuid4().hex[:8]}",
                    phase="grounding",
                    statement=f"Company {dim.replace('_', ' ')}: {val[:200]}",
                    supporting_evidence_ids=[
                        e.evidence_id for e in self._evidence[:5]
                    ],
                    confidence=self._compute_confidence(),
                    produced_by_agent=self._agent_id,
                ))
        return insights

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _ground_remaining(self) -> int:
        budget_cfg = self._config.get("budgets", {})
        query_budget = int(budget_cfg.get("external_search_query_budget", 5))
        used = self._budget.external_search_queries_used
        return max(0, query_budget - used)

    def _compute_confidence(self) -> float:
        filled = sum(
            1 for d in _DIMENSIONS
            if self._assessment.get(d, "unknown").lower() != "unknown"
        )
        return round(min(filled / len(_DIMENSIONS), 1.0), 2)

    def _build_summary(self) -> str:
        conf = self._compute_confidence()
        return (
            f"company_profiler: {self._steps_taken} steps, "
            f"{len(self._evidence)} evidence, "
            f"{conf:.0%} confidence"
        )
