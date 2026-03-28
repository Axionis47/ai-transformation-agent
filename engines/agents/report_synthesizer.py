"""ReportSynthesizer agent — produces final AdaptiveReport from hypotheses.

Unlike research agents, this runs ONE LLM call (no multi-step ReAct loop).
It receives validated hypotheses and their full reasoning chains, then
synthesizes everything into a coherent client-facing report.

v2: structured input with citable evidence and section-aware feedback.
"""
from __future__ import annotations

import json
from typing import Any

from core.events import EventType
from core.json_parser import extract_json
from core.schemas import (
    AdaptiveReport,
    AgentResult,
    Hypothesis,
    HypothesisStatus,
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
        previous_report: AdaptiveReport | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._hypotheses = hypotheses or []
        self._tracker = tracker or HypothesisTracker()
        self._feedback = feedback or []
        self._previous_report = previous_report

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
        structured, rejected, insights = self._build_structured_input()
        previous = ""
        if self._feedback and self._previous_report:
            previous = json.dumps(self._previous_report.model_dump(), indent=2, default=str)
        prompt = self._system_prompt.format(
            company_name=company, industry=industry,
            context_briefing=context_briefing,
            structured_hypotheses=structured, rejected_summary=rejected,
            key_insights=insights, previous_report=previous,
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

    def _build_structured_input(self) -> tuple[str, str, str]:
        """Returns (structured_hypotheses, rejected_summary, key_insights)."""
        validated = [h for h in self._hypotheses
                     if h.status in (HypothesisStatus.VALIDATED, HypothesisStatus.TESTING)]
        rejected = [h for h in self._hypotheses if h.status == HypothesisStatus.REJECTED]
        validated.sort(key=lambda h: h.confidence, reverse=True)
        blocks = [self._format_hypothesis_block(i, h) for i, h in enumerate(validated, 1)]
        structured = "\n\n".join(blocks) if blocks else "(No validated hypotheses)"
        return structured, self._format_rejected(rejected), self._format_insights()

    def _format_hypothesis_block(self, idx: int, h: Hypothesis) -> str:
        """Format one validated/testing hypothesis as a structured block."""
        ev_lines = self._gather_evidence_lines(h)
        chain = [f"{s.step_type}: {s.description[:100]}" for s in h.reasoning_chain]
        chain_text = " -> ".join(chain) if chain else "No chain recorded"
        conds = ", ".join(h.conditions_for_success[:3]) if h.conditions_for_success else "None identified"
        risks = ", ".join(h.risks[:3]) if h.risks else "None identified"
        label = "VALIDATED" if h.status == HypothesisStatus.VALIDATED else "TESTING"
        return (
            f"OPPORTUNITY {idx} [{label}, {h.confidence:.0%} confidence]:\n"
            f"  Statement: {h.statement}\n"
            f"  Category: {h.category} | Process: {h.target_process}\n"
            f"  Reasoning: {chain_text}\n"
            f"  Evidence:\n" + "\n".join(ev_lines) + "\n"
            f"  Conditions: {conds}\n"
            f"  Risks: {risks}"
        )

    def _gather_evidence_lines(self, h: Hypothesis) -> list[str]:
        """Query context provider for evidence relevant to a hypothesis."""
        if not self._ctx:
            return ["    - (no context provider)"]
        items = self._ctx.query_evidence(process_area=h.target_process, top_k=5)
        if not items:
            items = self._ctx.query_evidence(dimension="hypothesis_test", top_k=5)
        if not items:
            return ["    - (no evidence available)"]
        return [
            f"    - [{ev.evidence_id[:12]}] \"{ev.snippet[:120]}\" "
            f"({ev.source_type.value.replace('_', ' ').title()}, {ev.relevance_score:.2f})"
            for ev in items
        ]

    def _format_rejected(self, rejected: list[Hypothesis]) -> str:
        """One-line summaries of rejected hypotheses."""
        if not rejected:
            return "(None rejected)"
        return "\n".join(
            f"- \"{h.statement[:60]}\" — rejected: "
            f"{h.reasoning_chain[-1].description[:80] if h.reasoning_chain else 'insufficient evidence'}"
            for h in rejected
        )

    def _format_insights(self) -> str:
        """Key insights from the synthesis store."""
        insights = self._ctx.get_derived_insights() if self._ctx else []
        if not insights:
            return "(No derived insights)"
        return "\n".join(f"- {ins.statement} [{ins.confidence:.0%}]" for ins in insights[:8])

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
