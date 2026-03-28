"""Scoped context query interface for research agents.

Each agent gets an AgentContextProvider with a scope that controls what
prior-phase results it can see. Agents pull what they need — no data dumps.

Scope rules:
- COMPANY_PROFILER: sees intake only (fresh research start)
- INDUSTRY_ANALYST: sees intake only (parallel with profiler)
- PAIN_INVESTIGATOR: sees company + industry + grounding briefing
- HYPOTHESIS_FORMER: sees everything from prior phases + all insights
- HYPOTHESIS_TESTER: sees specific hypothesis + all evidence + insights
- REPORT_SYNTHESIZER: sees validated hypotheses + all insights + evidence
"""
from __future__ import annotations

from core.schemas import (
    AgentScope,
    CompanyIntake,
    CompanyUnderstanding,
    DerivedInsight,
    EvidenceItem,
    Hypothesis,
    HypothesisStatus,
    IndustryContext,
    PainPoint,
    Run,
)
from services.memory.synthesis_store import get_synthesis_store


# What each scope can access
_SCOPE_ACCESS = {
    AgentScope.COMPANY_PROFILER: {
        "intake", "evidence",
    },
    AgentScope.INDUSTRY_ANALYST: {
        "intake", "evidence",
    },
    AgentScope.PAIN_INVESTIGATOR: {
        "intake", "company_understanding", "industry_context",
        "briefings", "insights", "evidence",
    },
    AgentScope.HYPOTHESIS_FORMER: {
        "intake", "company_understanding", "industry_context",
        "pain_points", "briefings", "insights", "evidence",
    },
    AgentScope.HYPOTHESIS_TESTER: {
        "intake", "company_understanding", "industry_context",
        "pain_points", "hypotheses", "briefings", "insights", "evidence",
    },
    AgentScope.REPORT_SYNTHESIZER: {
        "intake", "company_understanding", "industry_context",
        "pain_points", "hypotheses", "briefings", "insights", "evidence",
    },
}


class AgentContextProvider:
    """Scoped, pull-based context for a research agent."""

    def __init__(self, run: Run, scope: AgentScope) -> None:
        self._run = run
        self._scope = scope
        self._access = _SCOPE_ACCESS[scope]
        self._synthesis = get_synthesis_store()

    @property
    def run_id(self) -> str:
        return self._run.run_id

    def get_intake(self) -> CompanyIntake | None:
        if "intake" not in self._access:
            return None
        return self._run.company_intake

    def get_company_understanding(self) -> CompanyUnderstanding | None:
        if "company_understanding" not in self._access:
            return None
        return self._run.company_understanding

    def get_industry_context(self) -> IndustryContext | None:
        if "industry_context" not in self._access:
            return None
        return self._run.industry_context

    def get_pain_points(self) -> list[PainPoint]:
        if "pain_points" not in self._access:
            return []
        return list(self._run.pain_points)

    def get_hypotheses(
        self, status: HypothesisStatus | None = None
    ) -> list[Hypothesis]:
        if "hypotheses" not in self._access:
            return []
        hyps = self._run.hypotheses
        if status is not None:
            return [h for h in hyps if h.status == status]
        return list(hyps)

    def get_phase_briefing(self, phase: str) -> str | None:
        if "briefings" not in self._access:
            return None
        return self._synthesis.get_phase_briefing(self._run.run_id, phase)

    def get_all_briefings(self) -> dict[str, str]:
        if "briefings" not in self._access:
            return {}
        return self._synthesis.get_all_briefings(self._run.run_id)

    def get_derived_insights(
        self, phase: str | None = None
    ) -> list[DerivedInsight]:
        if "insights" not in self._access:
            return []
        return self._synthesis.get_insights(self._run.run_id, phase=phase)

    def get_evidence(self) -> list[EvidenceItem]:
        if "evidence" not in self._access:
            return []
        return list(self._run.evidence)

    def query_evidence(
        self,
        dimension: str | None = None,
        process_area: str | None = None,
        top_k: int = 10,
    ) -> list[EvidenceItem]:
        """Query evidence with optional dimension/process filters, sorted by relevance."""
        if "evidence" not in self._access:
            return []
        items = list(self._run.evidence)
        if dimension:
            items = [e for e in items if e.dimension == dimension]
        if process_area:
            items = [e for e in items if e.process_area == process_area]
        items.sort(key=lambda e: e.relevance_score, reverse=True)
        return items[:top_k]

    def build_context_briefing(self) -> str:
        """Build a compact text briefing of everything this agent can see.

        Used as the primary context input for the agent's LLM prompt.
        Constant-size regardless of evidence count — briefings are compressed.
        """
        parts: list[str] = []

        intake = self.get_intake()
        if intake:
            parts.append(
                f"COMPANY: {intake.company_name} ({intake.industry})"
                + (f", {intake.employee_count_band} employees" if intake.employee_count_band else "")
                + (f"\nNotes: {intake.notes}" if intake.notes else "")
            )

        cu = self.get_company_understanding()
        if cu:
            parts.append(
                f"COMPANY UNDERSTANDING [{cu.confidence:.0%} confidence]:\n"
                f"  Does: {cu.what_they_do}\n"
                f"  Revenue: {cu.how_they_make_money}\n"
                f"  Scale: {cu.size_and_scale}\n"
                f"  Tech: {cu.technology_landscape}"
            )

        ic = self.get_industry_context()
        if ic:
            trends = ", ".join(ic.key_trends[:3]) if ic.key_trends else "unknown"
            parts.append(
                f"INDUSTRY [{ic.confidence:.0%} confidence]:\n"
                f"  Trends: {trends}\n"
                f"  AI adoption: {ic.ai_adoption_level}"
            )

        pps = self.get_pain_points()
        if pps:
            pp_lines = [f"  - {p.description} ({p.severity})" for p in pps[:5]]
            parts.append("PAIN POINTS:\n" + "\n".join(pp_lines))

        briefings = self.get_all_briefings()
        for phase, text in briefings.items():
            parts.append(f"BRIEFING ({phase}):\n  {text[:500]}")

        insights = self.get_derived_insights()
        if insights:
            insight_lines = [f"  - {i.statement} [{i.confidence:.0%}]" for i in insights[:10]]
            parts.append("DERIVED INSIGHTS:\n" + "\n".join(insight_lines))

        # Focused evidence summaries by dimension (top items only)
        for dim_tag in ("technology", "operations", "scale", "pain_point"):
            focused = self.query_evidence(dimension=dim_tag, top_k=3)
            if focused:
                lines = [f"  - {e.title}: {e.snippet[:120]}" for e in focused]
                parts.append(f"EVIDENCE ({dim_tag}):\n" + "\n".join(lines))

        return "\n\n".join(parts) if parts else "(no prior context available)"
