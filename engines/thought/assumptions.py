"""Assumption extraction — LLM-based, no keyword matching.

The model reads grounding text and extracts structured assumptions with
confidence reasoning and source quotes.
"""
from __future__ import annotations

from pathlib import Path

from core.json_parser import extract_json
from core.schemas import Assumption, AssumptionsDraft, EvidenceItem

_PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts"


def extract_assumptions_llm(
    grounding_text: str,
    evidence_items: list[EvidenceItem],
    grounder: object,
    run_id: str,
    company_name: str,
    industry: str,
) -> AssumptionsDraft:
    """Use LLM to extract structured assumptions from grounding text."""
    prompt_path = _PROMPT_DIR / "assumption_extraction.md"
    template = prompt_path.read_text()
    if template.startswith("---"):
        parts = template.split("---", 2)
        template = parts[2] if len(parts) > 2 else template

    evidence_lines: list[str] = []
    for e in evidence_items[:10]:
        evidence_lines.append(f"- [{e.source_type.value}] {e.title}: {e.snippet[:200]}")

    prompt = template
    prompt = prompt.replace("{company_name}", company_name)
    prompt = prompt.replace("{industry}", industry)
    prompt = prompt.replace("{grounding_text}", grounding_text)
    prompt = prompt.replace("{evidence_summary}", "\n".join(evidence_lines) or "No evidence sources.")
    prompt = prompt.replace("{{", "{").replace("}}", "}")

    raw_text = grounder.reason(prompt, run_id)  # type: ignore[attr-defined]
    parsed = extract_json(raw_text)

    assumptions: list[Assumption] = []
    for item in parsed.get("assumptions", []):
        assumptions.append(Assumption(
            field=item.get("field", "unknown"),
            value=item.get("value", ""),
            confidence=float(item.get("confidence", 0.5)),
            source="grounding",
        ))

    open_questions: list[str] = []
    for q in parsed.get("open_questions", []):
        if isinstance(q, dict):
            reason = q.get("reason", "")
            field = q.get("field", "")
            open_questions.append(f"{field}: {reason}" if field else reason)
        else:
            open_questions.append(str(q))

    return AssumptionsDraft(assumptions=assumptions, open_questions=open_questions)


def extract_assumptions(
    grounding_text: str,
    evidence_items: list[EvidenceItem],
) -> AssumptionsDraft:
    """Fallback extraction when no LLM client is available (e.g. budget exhausted)."""
    avg_confidence = (
        sum(e.confidence_score for e in evidence_items if e.confidence_score is not None)
        / max(1, sum(1 for e in evidence_items if e.confidence_score is not None))
        if evidence_items else 0.5
    )
    if avg_confidence == 0.0:
        avg_confidence = 0.5

    # Single assumption from full text rather than keyword matching
    if grounding_text.strip():
        assumptions = [Assumption(
            field="company_description",
            value=grounding_text[:300].strip(),
            confidence=round(avg_confidence, 4),
            source="grounding",
        )]
    else:
        assumptions = []

    return AssumptionsDraft(
        assumptions=assumptions,
        open_questions=[
            "Specific industry segment",
            "Approximate company size",
            "Main products or services",
            "Technology landscape",
            "How the company makes money",
        ],
    )
