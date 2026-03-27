"""PainPointInvestigator agent — discovers operational pain points.

Runs AFTER CompanyProfiler and IndustryAnalyst. Uses TWO tools:
GROUND (web search for company-specific pain evidence) and RAG
(past engagement knowledge base for similar pain patterns).
Returns typed AgentResult with pain_points list.
"""
from __future__ import annotations

import uuid

from core.json_parser import extract_json
from core.schemas import AgentResult, DerivedInsight, PainPoint
from engines.agents.base import AgentThought, BaseResearchAgent


class PainPointInvestigatorAgent(BaseResearchAgent):
    """Investigates operational pain points using grounding + RAG."""

    AGENT_TYPE = "pain_investigator"
    PROMPT_NAME = "agent_pain_investigator"
    MAX_STEPS = 8

    def __init__(self, **kwargs) -> None:  # type: ignore[override]
        super().__init__(**kwargs)
        agent_cfg = self._config.get("agents", {}).get("pain_investigator", {})
        self.MAX_STEPS = int(agent_cfg.get("max_steps", 8))
        self._past_queries: list[str] = []
        self._pain_points: list[dict] = []

    # ------------------------------------------------------------------
    # ReAct: THINK
    # ------------------------------------------------------------------
    async def _think(self, context: str) -> AgentThought:
        intake = self._ctx.get_intake() if self._ctx else None
        company = intake.company_name if intake else "unknown"
        industry = intake.industry if intake else "unknown"

        # Pull structured insights from grounding phase
        insights = self._ctx.get_derived_insights() if self._ctx else []
        insight_block = ""
        if insights:
            insight_lines = [
                f"- [{i.produced_by_agent}] {i.statement}"
                for i in insights
            ]
            insight_block = (
                "\nSTRUCTURED INSIGHTS FROM PRIOR PHASES:\n"
                + "\n".join(insight_lines)
            )

        prompt = self._system_prompt.format(
            company_name=company,
            industry=industry,
            context_briefing=context,
            ground_remaining=self._ground_remaining(),
            rag_remaining=self._rag_remaining(),
        )

        # Inject structured insights after context briefing
        if insight_block:
            prompt += insight_block

        if self._past_queries:
            prompt += "\n\nPrevious queries (do NOT repeat):\n"
            prompt += "\n".join(f"- {q}" for q in self._past_queries)

        if self._evidence:
            prompt += f"\n\nEvidence collected: {len(self._evidence)} items."

        raw = self._grounder.reason(prompt, self._run_id)
        if not raw:
            return AgentThought(action="STOP", reasoning="LLM returned empty")

        parsed = extract_json(raw)
        if not parsed or "action" not in parsed:
            return AgentThought(action="STOP", reasoning="unparseable response")

        action = parsed.get("action", "STOP").upper()
        query = parsed.get("query", "")
        reasoning = parsed.get("reasoning", "")

        # Accumulate pain points — LLM returns cumulative list each step
        pp_list = parsed.get("pain_points", [])
        if isinstance(pp_list, list) and pp_list:
            self._pain_points = pp_list

        if action in ("GROUND", "RAG") and query:
            if query in self._past_queries:
                return AgentThought(
                    action="STOP", reasoning="duplicate query — stopping"
                )
            self._past_queries.append(query)

        return AgentThought(
            action=action, query=query, reasoning=reasoning
        )

    # ------------------------------------------------------------------
    # Result builder
    # ------------------------------------------------------------------
    def _build_result(self, error: str | None = None) -> AgentResult:
        pain_points = self._build_pain_points()
        insights = self._build_derived_insights(pain_points)

        return AgentResult(
            agent_id=self._agent_id,
            agent_type=self.AGENT_TYPE,
            success=error is None,
            evidence_items=self._evidence,
            derived_insights=insights,
            summary=self._build_summary(),
            error=error,
            pain_points=pain_points,
        )

    def _build_pain_points(self) -> list[PainPoint]:
        evidence_ids = [e.evidence_id for e in self._evidence]
        result: list[PainPoint] = []
        for raw in self._pain_points:
            if not isinstance(raw, dict) or not raw.get("description"):
                continue
            result.append(PainPoint(
                pain_id=f"pp-{uuid.uuid4().hex[:8]}",
                description=raw.get("description", ""),
                affected_process=raw.get("affected_process", "general"),
                severity=raw.get("severity", "medium"),
                current_workaround=raw.get("current_workaround", ""),
                evidence_ids=evidence_ids[:5],
                confidence=self._compute_confidence(),
            ))
        return result

    def _build_derived_insights(
        self, pain_points: list[PainPoint]
    ) -> list[DerivedInsight]:
        insights: list[DerivedInsight] = []
        for pp in pain_points:
            insights.append(DerivedInsight(
                insight_id=f"ins-{uuid.uuid4().hex[:8]}",
                phase="pain_investigation",
                statement=(
                    f"Pain point in {pp.affected_process}: "
                    f"{pp.description} (severity: {pp.severity})"
                ),
                supporting_evidence_ids=pp.evidence_ids,
                confidence=pp.confidence,
                produced_by_agent=self._agent_id,
            ))
        return insights

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _ground_remaining(self) -> int:
        budget_cfg = self._config.get("budgets", {})
        cap = int(budget_cfg.get("external_search_query_budget", 5))
        return max(0, cap - self._budget.external_search_queries_used)

    def _rag_remaining(self) -> int:
        budget_cfg = self._config.get("budgets", {})
        cap = int(budget_cfg.get("rag_query_budget", 8))
        return max(0, cap - self._budget.rag_queries_used)

    def _compute_confidence(self) -> float:
        if not self._evidence:
            return 0.3
        count = min(len(self._evidence), 10)
        return round(0.3 + (count * 0.06), 2)

    def _build_summary(self) -> str:
        n = len(self._pain_points)
        return (
            f"pain_investigator: {self._steps_taken} steps, "
            f"{len(self._evidence)} evidence, "
            f"{n} pain points"
        )
