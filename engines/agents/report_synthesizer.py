"""ReportSynthesizer agent — produces final AdaptiveReport from hypotheses.

Unlike research agents, this runs ONE LLM call (no multi-step ReAct loop).
It receives validated hypotheses and their full reasoning chains, then
synthesizes everything into a coherent client-facing report.
"""
from __future__ import annotations

from typing import Any

from core.events import EventType
from core.json_parser import extract_json
from core.schemas import (
    AdaptiveReport,
    AgentResult,
    Hypothesis,
    ReportFeedback,
    ReportOpportunity,
)
from engines.agents.base import AgentThought, BaseResearchAgent
from engines.hypothesis_tracker import HypothesisTracker
from services.trace import emit


class ReportSynthesizerAgent(BaseResearchAgent):
    """Single-shot synthesis: hypotheses + evidence -> AdaptiveReport."""

    AGENT_TYPE = "report_synthesizer"
    PROMPT_NAME = "agent_report_synthesizer"
    MAX_STEPS = 1

    def __init__(
        self,
        hypotheses: list[Hypothesis] | None = None,
        tracker: HypothesisTracker | None = None,
        feedback: list[ReportFeedback] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._hypotheses = hypotheses or []
        self._tracker = tracker or HypothesisTracker()
        self._feedback = feedback or []

    async def run(self) -> AgentResult:
        """Single synthesis call — no ReAct loop."""
        emit(self._run_id, EventType.AGENT_SPAWNED, {
            "agent_id": self._agent_id,
            "agent_type": self.AGENT_TYPE,
            "hypotheses_count": len(self._hypotheses),
        })

        try:
            context_briefing = ""
            if self._ctx:
                context_briefing = self._ctx.build_context_briefing()

            prompt = self._build_synthesis_prompt(context_briefing)
            raw = self._grounder.reason(prompt, self._run_id)
            self._steps_taken = 1

            report = self._parse_report(raw)

            emit(self._run_id, EventType.AGENT_COMPLETED, {
                "agent_id": self._agent_id,
                "opportunities": len(report.opportunities),
                "key_insight": report.key_insight[:100],
            })
            return self._build_result(report=report)

        except Exception as e:
            emit(self._run_id, EventType.AGENT_FAILED, {
                "agent_id": self._agent_id,
                "error": str(e),
            })
            fallback = self._fallback_report()
            return self._build_result(report=fallback, error=str(e))

    def _build_synthesis_prompt(self, context_briefing: str) -> str:
        intake = self._ctx.get_intake() if self._ctx else None
        company = intake.company_name if intake else "unknown"
        industry = intake.industry if intake else "unknown"

        hyp_summary = self._build_hypotheses_summary()
        chains = self._build_reasoning_chains()
        ev_count = sum(len(h.evidence_for) for h in self._hypotheses)

        prompt = self._system_prompt.format(
            company_name=company,
            industry=industry,
            context_briefing=context_briefing,
            hypotheses_summary=hyp_summary,
            reasoning_chains=chains,
            evidence_count=ev_count,
        )

        if self._feedback:
            prompt += self._build_feedback_section()
        return prompt

    def _build_feedback_section(self) -> str:
        """Append user feedback instructions to the prompt."""
        lines = [
            "\n\n## USER FEEDBACK — INCORPORATE THESE CHANGES",
            "The user has reviewed the previous version of this "
            "report and wants specific changes:\n",
        ]
        for i, fb in enumerate(self._feedback, 1):
            lines.append(
                f"{i}. [{fb.feedback_type}] Target: "
                f"{fb.target_section} — \"{fb.instruction}\""
            )
        lines.append(
            "\nRegenerate the report incorporating ALL feedback. "
            "Keep everything else that was good."
        )
        return "\n".join(lines)

    def _build_hypotheses_summary(self) -> str:
        if not self._hypotheses:
            return "(no hypotheses available)"
        parts: list[str] = []
        for h in self._hypotheses:
            narrative = self._tracker.get_full_narrative(h.hypothesis_id)
            parts.append(narrative)
        return "\n\n".join(parts)

    def _build_reasoning_chains(self) -> str:
        if not self._hypotheses:
            return "(no reasoning chains)"
        lines: list[str] = []
        for h in self._hypotheses:
            for step in h.reasoning_chain:
                lines.append(
                    f"[{h.hypothesis_id}] {step.step_type}: "
                    f"{step.description}"
                )
        return "\n".join(lines) if lines else "(no steps recorded)"

    def _parse_report(self, raw: str) -> AdaptiveReport:
        parsed = extract_json(raw)
        report_data = parsed.get("report", parsed)

        if not report_data or not report_data.get("executive_summary"):
            return self._fallback_report()

        opps = self._parse_opportunities(report_data.get("opportunities", []))

        return AdaptiveReport(
            run_id=self._run_id,
            executive_summary=report_data.get("executive_summary", ""),
            key_insight=report_data.get("key_insight", ""),
            opportunities=opps,
            reasoning_chain=report_data.get("reasoning_chain", []),
            confidence_assessment=report_data.get("confidence_assessment", ""),
            what_we_dont_know=report_data.get("what_we_dont_know", []),
            recommended_next_steps=report_data.get("recommended_next_steps", []),
        )

    def _parse_opportunities(self, raw_opps: list) -> list[ReportOpportunity]:
        result: list[ReportOpportunity] = []
        for item in raw_opps:
            if not isinstance(item, dict):
                continue
            result.append(ReportOpportunity(
                title=item.get("title", "Untitled"),
                hypothesis_id=item.get("hypothesis_id", "unknown"),
                narrative=item.get("narrative", ""),
                tier=item.get("tier", "medium"),
                confidence=float(item.get("confidence", 0.5)),
                evidence_summary=item.get("evidence_summary", ""),
                risks=item.get("risks", []),
                conditions_for_success=item.get("conditions_for_success", []),
                recommended_approach=item.get("recommended_approach", ""),
            ))
        return result

    def _fallback_report(self) -> AdaptiveReport:
        opps = [
            ReportOpportunity(
                title=h.statement,
                hypothesis_id=h.hypothesis_id,
                narrative=self._tracker.get_full_narrative(h.hypothesis_id),
                tier="medium",
                confidence=h.confidence,
            )
            for h in self._hypotheses
        ]
        return AdaptiveReport(
            run_id=self._run_id,
            executive_summary="Report generated from available hypotheses.",
            key_insight=self._hypotheses[0].statement if self._hypotheses else "",
            opportunities=opps,
            what_we_dont_know=["LLM synthesis unavailable — raw data used"],
        )

    def _build_result(
        self,
        report: AdaptiveReport | None = None,
        error: str | None = None,
    ) -> AgentResult:
        return AgentResult(
            agent_id=self._agent_id,
            agent_type=self.AGENT_TYPE,
            success=error is None,
            evidence_items=self._evidence,
            derived_insights=self._insights,
            summary=self._build_summary(),
            error=error,
            adaptive_report=report,
        )

    def _build_summary(self) -> str:
        n = len(self._hypotheses)
        return f"report_synthesizer: {n} hypotheses synthesized into report"

    async def _think(self, context: str) -> AgentThought:
        return AgentThought(action="STOP", reasoning="single-shot agent")
