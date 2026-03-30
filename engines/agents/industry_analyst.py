"""IndustryAnalyst agent — builds a factual IndustryContext.

Runs a ReAct loop: THINK (ask LLM what to search) → ACT (ground via
Google Search) → OBSERVE (accumulate evidence) → repeat until confident
or budget exhausted. Returns typed AgentResult with IndustryContext.

Runs in PARALLEL with CompanyProfiler — fully independent, no shared state.
"""

from __future__ import annotations

import uuid

from core.json_parser import extract_json
from core.schemas import AgentResult, DerivedInsight, IndustryContext
from engines.agents.base import AgentThought, BaseResearchAgent

_DIMENSIONS = [
    "key_trends",
    "competitive_dynamics",
    "regulatory_landscape",
    "ai_adoption_level",
]


class IndustryAnalystAgent(BaseResearchAgent):
    """Analyses an industry across four dimensions using grounded search."""

    AGENT_TYPE = "industry_analyst"
    PROMPT_NAME = "agent_industry_analyst"

    def __init__(self, **kwargs) -> None:  # type: ignore[override]
        super().__init__(**kwargs)
        if self._max_steps_override is not None:
            self.MAX_STEPS = self._max_steps_override
        else:
            agent_cfg = self._config.get("agents", {}).get("industry_analyst", {})
            self.MAX_STEPS = int(agent_cfg.get("max_steps", 6))
        self._past_queries: list[str] = []
        self._current_dimension: str = "industry"
        self._assessment: dict[str, str | list[str]] = {
            "key_trends": [],
            "competitive_dynamics": "",
            "regulatory_landscape": "",
            "ai_adoption_level": "",
        }

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
            trends = assessment.get("key_trends")
            if isinstance(trends, list) and trends:
                self._assessment["key_trends"] = trends
            for dim in ("competitive_dynamics", "regulatory_landscape", "ai_adoption_level"):
                val = assessment.get(dim)
                if val and isinstance(val, str) and val.strip():
                    self._assessment[dim] = val

        if action == "GROUND" and query:
            if query in self._past_queries:
                return AgentThought(action="STOP", reasoning="duplicate query — stopping")
            self._past_queries.append(query)

        return AgentThought(action=action, query=query, reasoning=reasoning)

    # ------------------------------------------------------------------
    # ReAct: OBSERVE — tag new evidence with industry dimension
    # ------------------------------------------------------------------
    def _observe(self, observation: str) -> None:
        for ev in self._evidence[self._prev_evidence_count :]:
            ev.dimension = "industry"
            ev.produced_by = self._agent_id

    # ------------------------------------------------------------------
    # Result builder
    # ------------------------------------------------------------------
    def _build_result(self, error: str | None = None) -> AgentResult:
        confidence = self._compute_confidence()
        intake = self._ctx.get_intake() if self._ctx else None

        trends_raw = self._assessment.get("key_trends", [])
        trends = trends_raw if isinstance(trends_raw, list) else []

        ic = IndustryContext(
            industry=intake.industry if intake else "unknown",
            key_trends=trends,
            competitive_dynamics=str(self._assessment.get("competitive_dynamics", "")),
            regulatory_landscape=str(self._assessment.get("regulatory_landscape", "")),
            ai_adoption_level=str(self._assessment.get("ai_adoption_level", "")),
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
            industry_context=ic,
        )

    def _build_derived_insights(self) -> list[DerivedInsight]:
        insights: list[DerivedInsight] = []
        trends = self._assessment.get("key_trends", [])
        if isinstance(trends, list) and trends:
            insights.append(
                DerivedInsight(
                    insight_id=f"ins-{uuid.uuid4().hex[:8]}",
                    phase="grounding",
                    statement=f"Industry trends: {', '.join(trends[:3])}",
                    supporting_evidence_ids=[e.evidence_id for e in self._evidence[:5]],
                    confidence=self._compute_confidence(),
                    produced_by_agent=self._agent_id,
                )
            )
        for dim in ("competitive_dynamics", "regulatory_landscape", "ai_adoption_level"):
            val = self._assessment.get(dim, "")
            if isinstance(val, str) and val.strip():
                insights.append(
                    DerivedInsight(
                        insight_id=f"ins-{uuid.uuid4().hex[:8]}",
                        phase="grounding",
                        statement=(f"Industry {dim.replace('_', ' ')}: {val[:200]}"),
                        supporting_evidence_ids=[e.evidence_id for e in self._evidence[:5]],
                        confidence=self._compute_confidence(),
                        produced_by_agent=self._agent_id,
                    )
                )
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
        filled = 0
        trends = self._assessment.get("key_trends", [])
        if isinstance(trends, list) and len(trends) > 0:
            filled += 1
        for dim in ("competitive_dynamics", "regulatory_landscape", "ai_adoption_level"):
            val = self._assessment.get(dim, "")
            if isinstance(val, str) and val.strip():
                filled += 1
        return round(min(filled / len(_DIMENSIONS), 1.0), 2)

    def _build_summary(self) -> str:
        conf = self._compute_confidence()
        return f"industry_analyst: {self._steps_taken} steps, {len(self._evidence)} evidence, {conf:.0%} confidence"
