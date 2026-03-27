"""Template matching — LLM-based evaluation.

No keyword signal counting. The model evaluates each template's fit
against accumulated evidence and returns structured scores.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.json_parser import extract_json
from core.schemas import AssumptionsDraft, CompanyIntake, EvidenceItem, EvidenceSource
from engines.pitch.templates import OpportunityTemplate

_PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts"


@dataclass
class TemplateMatch:
    template: OpportunityTemplate
    match_score: float
    win_signal_hits: list[str] = field(default_factory=list)
    anti_signal_hits: list[str] = field(default_factory=list)
    matched_evidence_ids: list[str] = field(default_factory=list)
    matched_engagement_ids: list[str] = field(default_factory=list)
    # LLM-provided fields
    tier_override: str | None = None
    reasoning: str = ""
    risks: list[str] = field(default_factory=list)
    adaptation_needed: str | None = None
    llm_scores: dict = field(default_factory=dict)


def _build_evidence_text(evidence: list[EvidenceItem]) -> str:
    lines: list[str] = []
    for e in evidence[:15]:
        line = f"- [id={e.evidence_id}] [{e.source_type.value}] {e.title}: {e.snippet[:200]}"
        # Include cross-reference findings from reasoning loop
        crossref = e.retrieval_meta.get("crossref")
        if crossref:
            line += f"\n    Cross-ref: {crossref.get('relevance', '')}"
            conds = crossref.get("conditions_check", [])
            met = sum(1 for c in conds if c.get("status") == "MET")
            unmet = sum(1 for c in conds if c.get("status") == "UNMET")
            unknown = sum(1 for c in conds if c.get("status") == "UNKNOWN")
            if conds:
                line += f"\n    Conditions: {met} met, {unmet} unmet, {unknown} unknown"
            triggered = [a.get("pattern", "") for a in crossref.get("anti_pattern_check", []) if a.get("status") == "TRIGGERED"]
            if triggered:
                line += f"\n    Anti-patterns triggered: {', '.join(triggered[:2])}"
        lines.append(line)
    return "\n".join(lines) or "No evidence collected."


def _build_engagement_summary(
    template: OpportunityTemplate, engagement_lookup: dict[str, dict],
    evidence: list[EvidenceItem] | None = None,
) -> str:
    """Build engagement summary including cross-ref data from reasoning loop."""
    lines: list[str] = []

    # First: show cross-referenced engagements found during reasoning
    if evidence:
        for e in evidence:
            crossref = e.retrieval_meta.get("crossref")
            if crossref and e.source_ref in template.engagement_ids:
                eng_id = crossref.get("engagement_id", e.source_ref)
                lines.append(
                    f"- {eng_id}: {crossref.get('engagement_title', 'Unknown')} "
                    f"[CROSS-REFERENCED DURING RESEARCH]\n"
                    f"    Relevance: {crossref.get('relevance', 'Unknown')}\n"
                    f"    Transferable: {crossref.get('transferable', [])}\n"
                    f"    Needs adaptation: {crossref.get('needs_adaptation', [])}\n"
                    f"    Impact: {crossref.get('measured_impact', {})}"
                )

    # Then: show remaining linked engagements not cross-referenced
    shown_ids = {e.source_ref for e in (evidence or []) if e.retrieval_meta.get("crossref")}
    for eng_id in template.engagement_ids:
        if eng_id in shown_ids:
            continue
        eng = engagement_lookup.get(eng_id)
        if eng:
            lines.append(
                f"- {eng_id}: {eng.get('title', 'Unknown')} "
                f"(industry: {eng.get('industry', '?')}, "
                f"impact: {eng.get('measured_impact', {})})"
            )
    return "\n".join(lines) or "No past engagements linked."


def _build_reasoning_context(evidence: list[EvidenceItem]) -> str:
    """Summarize what the reasoning loop found — cross-refs, coverage gaps."""
    crossrefs: list[str] = []
    for e in evidence:
        cr = e.retrieval_meta.get("crossref")
        if cr:
            eng_title = cr.get("engagement_title", "Unknown")
            relevance = cr.get("relevance", "")
            risks = cr.get("implementation_risks", [])
            baseline = cr.get("baseline_comparison", "")
            line = f"- {eng_title}: {relevance}"
            if risks:
                line += f"\n  Implementation risk: {risks[0][:150]}"
            if baseline:
                line += f"\n  Baseline comparison: {baseline[:150]}"
            crossrefs.append(line)
    if not crossrefs:
        return "No past engagements were cross-referenced during research."
    return "During research, these past engagements were cross-referenced against the company:\n" + "\n".join(crossrefs)


def match_templates_llm(
    evidence: list[EvidenceItem],
    templates: list[OpportunityTemplate],
    intake: CompanyIntake,
    assumptions: AssumptionsDraft,
    grounder: object,
    run_id: str,
    engagement_lookup: dict[str, dict],
) -> list[TemplateMatch]:
    """Evaluate each template against evidence using the LLM."""
    prompt_path = _PROMPT_DIR / "opportunity_evaluation.md"
    template_text = prompt_path.read_text()
    if template_text.startswith("---"):
        parts = template_text.split("---", 2)
        template_text = parts[2] if len(parts) > 2 else template_text

    assumptions_lines: list[str] = []
    for a in assumptions.assumptions:
        assumptions_lines.append(f"- {a.field}: {a.value} (confidence: {a.confidence})")

    evidence_text = _build_evidence_text(evidence)
    matches: list[TemplateMatch] = []

    for tmpl in templates:
        prompt = template_text
        prompt = prompt.replace("{company_name}", intake.company_name)
        prompt = prompt.replace("{industry}", intake.industry)
        prompt = prompt.replace("{employee_count_band}", intake.employee_count_band or "unknown")
        prompt = prompt.replace("{assumptions_summary}", "\n".join(assumptions_lines) or "None.")
        prompt = prompt.replace("{template_name}", tmpl.name)
        prompt = prompt.replace("{template_description}", tmpl.description)
        prompt = prompt.replace("{solution_shape}", tmpl.solution_shape)
        prompt = prompt.replace("{workflow_area}", tmpl.workflow_area)
        prompt = prompt.replace("{timeline_weeks}", str(tmpl.typical_timeline_weeks))
        prompt = prompt.replace("{applicable_industries}", ", ".join(tmpl.applicable_industries))
        prompt = prompt.replace("{engagement_summaries}", _build_engagement_summary(tmpl, engagement_lookup, evidence))
        prompt = prompt.replace("{evidence_items}", evidence_text)
        prompt = prompt.replace("{reasoning_context}", _build_reasoning_context(evidence))
        prompt = prompt.replace("{{", "{").replace("}}", "}")

        raw_text = grounder.reason(prompt, run_id)  # type: ignore[attr-defined]
        parsed = extract_json(raw_text)

        fit_score = float(parsed.get("fit_score", 0.0))
        if fit_score < 0.35:
            continue

        # Extract evidence and engagement IDs from LLM response
        supporting_ids = parsed.get("supporting_evidence_ids", [])
        engagement_ids = parsed.get("matched_engagement_ids", [])
        # Also include any WINS_KB evidence IDs automatically
        for e in evidence:
            if (
                e.source_type == EvidenceSource.WINS_KB
                and e.source_ref
                and e.source_ref not in engagement_ids
            ):
                engagement_ids.append(e.source_ref)

        matches.append(TemplateMatch(
            template=tmpl,
            match_score=round(fit_score, 4),
            matched_evidence_ids=supporting_ids,
            matched_engagement_ids=engagement_ids,
            tier_override=parsed.get("tier"),
            reasoning=parsed.get("reasoning", ""),
            risks=parsed.get("risks", []),
            adaptation_needed=parsed.get("adaptation_needed"),
            llm_scores={
                "feasibility": float(parsed.get("feasibility", 0.5)),
                "roi": float(parsed.get("roi_score", 0.5)),
                "time_to_value": float(parsed.get("time_to_value", 0.5)),
                "confidence": float(parsed.get("confidence", 0.3)),
            },
        ))

    matches.sort(key=lambda m: m.match_score, reverse=True)
    return matches


def match_templates(
    evidence: list[EvidenceItem],
    templates: list[OpportunityTemplate],
) -> list[TemplateMatch]:
    """Fallback: basic matching without LLM (used when no client available)."""
    matches: list[TemplateMatch] = []
    for tmpl in templates:
        evidence_ids = [e.evidence_id for e in evidence[:5]]
        engagement_ids = [
            e.source_ref for e in evidence
            if e.source_type == EvidenceSource.WINS_KB and e.source_ref
        ]
        if evidence:
            avg_score = sum(e.relevance_score for e in evidence) / len(evidence)
            matches.append(TemplateMatch(
                template=tmpl,
                match_score=round(avg_score * 0.5, 4),
                matched_evidence_ids=evidence_ids,
                matched_engagement_ids=engagement_ids,
            ))
    matches.sort(key=lambda m: m.match_score, reverse=True)
    return matches[:5]
