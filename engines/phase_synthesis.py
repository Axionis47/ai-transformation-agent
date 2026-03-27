"""Inter-phase synthesis: compresses phase outputs into briefings.

Called by the orchestrator BETWEEN phases. The compressed briefing becomes
the primary context for the next phase's agents — not raw evidence dumps.

Uses real LLM (grounder.reason()) to compress, NOT just concatenation.
"""
from __future__ import annotations

from pathlib import Path

from core.schemas import (
    CompanyUnderstanding,
    DerivedInsight,
    EvidenceItem,
    Hypothesis,
    IndustryContext,
    PainPoint,
)
from services.memory.synthesis_store import SynthesisStore


_PROMPT_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    path = _PROMPT_DIR / f"{name}.md"
    if not path.exists():
        return ""
    text = path.read_text()
    if text.startswith("---"):
        parts = text.split("---", 2)
        text = parts[2] if len(parts) > 2 else text
    return text.strip()


class PhaseSynthesizer:
    """Compresses phase outputs into constant-size briefings via LLM."""

    def __init__(self, grounder: object, synthesis_store: SynthesisStore) -> None:
        self._grounder = grounder
        self._store = synthesis_store

    async def synthesize_grounding(
        self,
        run_id: str,
        company: CompanyUnderstanding | None,
        industry: IndustryContext | None,
        evidence: list[EvidenceItem],
    ) -> str:
        """Compress GROUNDING phase → briefing for DEEP_RESEARCH."""
        context_parts = []
        if company:
            context_parts.append(
                f"Company: {company.company_name}\n"
                f"What they do: {company.what_they_do}\n"
                f"Revenue model: {company.how_they_make_money}\n"
                f"Scale: {company.size_and_scale}\n"
                f"Tech landscape: {company.technology_landscape}\n"
                f"Confidence: {company.confidence:.0%}"
            )
        if industry:
            trends = ", ".join(industry.key_trends[:5])
            context_parts.append(
                f"Industry: {industry.industry}\n"
                f"Trends: {trends}\n"
                f"Competitive dynamics: {industry.competitive_dynamics}\n"
                f"AI adoption: {industry.ai_adoption_level}\n"
                f"Confidence: {industry.confidence:.0%}"
            )
        if evidence:
            snippets = [f"- {e.title}: {e.snippet[:150]}" for e in evidence[:10]]
            context_parts.append("Key evidence:\n" + "\n".join(snippets))

        context = "\n\n".join(context_parts)
        prompt = (
            "You are a senior analyst synthesizing research findings into a concise briefing.\n\n"
            "RESEARCH FINDINGS:\n" + context + "\n\n"
            "Write a 3-5 sentence briefing that captures:\n"
            "1. What the company does and its scale\n"
            "2. Key technology and operational characteristics\n"
            "3. Industry context that matters for AI opportunities\n"
            "4. Any gaps or uncertainties in our understanding\n\n"
            "Be specific and factual. No filler. Every sentence must add information."
        )
        briefing = self._grounder.reason(prompt, run_id)  # type: ignore[attr-defined]
        if briefing:
            self._store.save_phase_briefing(run_id, "grounding", briefing)
        return briefing or context[:500]

    async def synthesize_research(
        self,
        run_id: str,
        pain_points: list[PainPoint],
        grounding_briefing: str,
        evidence: list[EvidenceItem],
        insights: list[DerivedInsight],
    ) -> str:
        """Compress DEEP_RESEARCH phase → briefing for HYPOTHESIS_FORMATION."""
        context_parts = [f"PRIOR BRIEFING:\n{grounding_briefing}"]
        if pain_points:
            pp_text = "\n".join(
                f"- {p.description} (severity: {p.severity}, process: {p.affected_process})"
                for p in pain_points
            )
            context_parts.append(f"PAIN POINTS IDENTIFIED:\n{pp_text}")
        if insights:
            ins_text = "\n".join(
                f"- {i.statement} [{i.confidence:.0%} confidence]"
                for i in insights
            )
            context_parts.append(f"DERIVED INSIGHTS:\n{ins_text}")

        context = "\n\n".join(context_parts)
        prompt = (
            "You are a senior analyst preparing a briefing for the hypothesis formation phase.\n\n"
            "RESEARCH SO FAR:\n" + context + "\n\n"
            "Write a 4-6 sentence briefing that captures:\n"
            "1. Company overview (from prior briefing)\n"
            "2. Most significant pain points and their business impact\n"
            "3. Which pain points are most amenable to AI solutions and why\n"
            "4. What evidence is strong vs. what needs more investigation\n\n"
            "Focus on actionability — what should we hypothesize about?"
        )
        briefing = self._grounder.reason(prompt, run_id)  # type: ignore[attr-defined]
        if briefing:
            self._store.save_phase_briefing(run_id, "deep_research", briefing)
        return briefing or context[:500]

    async def synthesize_testing(
        self,
        run_id: str,
        hypotheses: list[Hypothesis],
        insights: list[DerivedInsight],
    ) -> str:
        """Compress HYPOTHESIS_TESTING → briefing for SYNTHESIS/REPORT."""
        hyp_text = []
        for h in hypotheses:
            status_label = h.status.value.upper()
            chain_summary = " → ".join(
                s.step_type for s in h.reasoning_chain
            )
            hyp_text.append(
                f"- [{status_label}] {h.statement} "
                f"(confidence: {h.confidence:.0%}, chain: {chain_summary})"
            )

        context = "HYPOTHESES TESTED:\n" + "\n".join(hyp_text)
        if insights:
            context += "\n\nKEY INSIGHTS:\n" + "\n".join(
                f"- {i.statement}" for i in insights[:10]
            )

        prompt = (
            "You are a senior analyst preparing the final synthesis briefing.\n\n"
            + context + "\n\n"
            "Write a 3-5 sentence briefing that captures:\n"
            "1. Which hypotheses were validated and why\n"
            "2. Which were rejected and what we learned from that\n"
            "3. Overall confidence level in our recommendations\n"
            "4. Key remaining uncertainties\n\n"
            "This briefing feeds directly into the final report."
        )
        briefing = self._grounder.reason(prompt, run_id)  # type: ignore[attr-defined]
        if briefing:
            self._store.save_phase_briefing(run_id, "hypothesis_testing", briefing)
        return briefing or context[:500]
