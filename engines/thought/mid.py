"""Missing Information Detection — LLM-based coverage assessment.

No keyword matching. The model reasons about what's known and what's missing.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.json_parser import extract_json
from core.schemas import BudgetState, EvidenceItem

REQUIRED_FIELDS = [
    "company_profile",
    "industry_context",
    "business_processes",
    "pain_points",
    "similar_wins",
    "scale_indicators",
]

_PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts"


@dataclass
class MIDGap:
    field: str
    coverage: float
    action: str
    query: str = ""
    thinking: str = ""


def _build_evidence_summary(evidence: list[EvidenceItem]) -> str:
    if not evidence:
        return "No evidence collected yet."
    lines: list[str] = []
    # Top 5 evidence items get full detail (up to 500 chars)
    for e in evidence[:5]:
        line = f"- [{e.source_type.value}] {e.title}: {e.snippet[:500]}"
        crossref = e.retrieval_meta.get("crossref")
        if crossref:
            line += f"\n  [Cross-ref: {crossref.get('relevance', '')}]"
        lines.append(line)
    # Remaining items get short summaries
    for e in evidence[5:12]:
        lines.append(f"- [{e.source_type.value}] {e.title}: {e.snippet[:150]}")
    if len(evidence) > 12:
        lines.append(f"  ... and {len(evidence) - 12} more evidence items")
    return "\n".join(lines)


def _build_field_coverage_table(field_coverage: dict[str, float]) -> str:
    lines: list[str] = []
    for field in REQUIRED_FIELDS:
        score = field_coverage.get(field, 0.0)
        bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
        lines.append(f"  {field:25s} {bar} {score:.1%}")
    return "\n".join(lines)


def assess_coverage_with_llm(
    evidence: list[EvidenceItem],
    config: dict,
    grounder: object,
    run_id: str,
    intake: object,
    assumptions: object,
    prior_reasoning: list[str] | None = None,
) -> tuple[dict[str, float], float, MIDGap | None]:
    """Use the LLM to assess coverage, confidence, and decide next action.

    Returns (field_coverage, overall_confidence, gap_or_none).
    """
    budget_state: BudgetState = config.get("_budget_state", BudgetState())
    budgets = config.get("budgets", {})
    ground_total = int(budgets.get("external_search_query_budget", 5))
    rag_total = int(budgets.get("rag_query_budget", 8))
    ground_remaining = max(0, ground_total - budget_state.external_search_queries_used)
    rag_remaining = max(0, rag_total - budget_state.rag_queries_used)

    # Build current coverage estimate from evidence density per field
    field_coverage = _estimate_field_coverage(evidence)
    overall = sum(field_coverage.values()) / max(len(REQUIRED_FIELDS), 1)

    # Load ReAct prompt
    prompt_path = _PROMPT_DIR / "reasoning_react.md"
    template = prompt_path.read_text()
    if template.startswith("---"):
        parts = template.split("---", 2)
        template = parts[2] if len(parts) > 2 else template

    company_name = getattr(intake, "company_name", "the company")
    industry = getattr(intake, "industry", "the industry")
    assumptions_lines: list[str] = []
    if assumptions and hasattr(assumptions, "assumptions"):
        for a in assumptions.assumptions:
            assumptions_lines.append(f"- {a.field}: {a.value} (confidence: {a.confidence})")

    # Use replace instead of .format() to avoid issues with curly braces in values
    prompt = template
    prompt = prompt.replace("{company_name}", company_name)
    prompt = prompt.replace("{industry}", industry)
    prompt = prompt.replace("{evidence_summary}", _build_evidence_summary(evidence))
    prompt = prompt.replace("{field_coverage_table}", _build_field_coverage_table(field_coverage))
    prompt = prompt.replace("{assumptions_summary}", "\n".join(assumptions_lines) or "None confirmed yet.")
    reasoning_text = "No prior steps yet — this is the first reasoning loop."
    if prior_reasoning:
        reasoning_text = "\n".join(f"Loop {i}: {r[:200]}" for i, r in enumerate(prior_reasoning))
    prompt = prompt.replace("{prior_reasoning}", reasoning_text)
    prompt = prompt.replace("{ground_remaining}", str(ground_remaining))
    prompt = prompt.replace("{ground_total}", str(ground_total))
    prompt = prompt.replace("{rag_remaining}", str(rag_remaining))
    prompt = prompt.replace("{rag_total}", str(rag_total))
    # Convert escaped braces back for JSON example
    prompt = prompt.replace("{{", "{").replace("}}", "}")

    raw_text = grounder.reason(prompt, run_id)  # type: ignore[attr-defined]
    parsed = extract_json(raw_text)

    from services.trace import emit as _emit
    from core.events import EventType as _ET
    _emit(run_id, _ET.REASONING_LOOP_STARTED, {
        "react_raw_length": len(raw_text),
        "react_parsed_keys": list(parsed.keys()),
        "react_action": parsed.get("action", "NONE"),
        "react_thinking": str(parsed.get("thinking", ""))[:200],
    })

    action = parsed.get("action", "STOP").upper()

    # If LLM call failed (empty response), fall back to tool-based actions
    # instead of defaulting to STOP with zero evidence
    if not raw_text and not evidence:
        # No evidence yet and LLM failed — try grounding first, then RAG
        if ground_remaining > 0:
            action = "GROUND"
            parsed = {"query": f"What does {company_name} do and what challenges do they face in {industry}?",
                      "target_field": "company_profile", "thinking": "LLM reasoning unavailable, using fallback query"}
        elif rag_remaining > 0:
            action = "RAG"
            parsed = {"query": f"{industry} automation implementation",
                      "target_field": "similar_wins", "thinking": "LLM reasoning unavailable, searching past engagements"}
    elif not raw_text and evidence:
        # Have evidence but LLM failed — try RAG if not used yet, else STOP gracefully
        if rag_remaining > 0:
            action = "RAG"
            parsed = {"query": f"{industry} {company_name} automation",
                      "target_field": "similar_wins", "thinking": "LLM reasoning unavailable, searching for similar past cases"}
        else:
            action = "STOP"
    if action == "STOP":
        return field_coverage, overall, None

    # Map action to gap
    action_map = {"GROUND": "ground", "RAG": "rag", "ASK_USER": "ask_user"}
    gap_action = action_map.get(action, "ask_user")

    # Budget enforcement: if model chose a tool that's exhausted, fall back
    if gap_action == "ground" and ground_remaining <= 0:
        gap_action = "rag" if rag_remaining > 0 else "ask_user"
    if gap_action == "rag" and rag_remaining <= 0:
        gap_action = "ask_user"

    target_field = parsed.get("target_field", "company_profile")
    if target_field not in REQUIRED_FIELDS:
        target_field = "company_profile"

    gap = MIDGap(
        field=target_field,
        coverage=field_coverage.get(target_field, 0.0),
        action=gap_action,
        query=parsed.get("query", ""),
        thinking=parsed.get("thinking", ""),
    )
    return field_coverage, overall, gap


def _estimate_field_coverage(evidence: list[EvidenceItem]) -> dict[str, float]:
    """Lightweight coverage estimate based on evidence count per source type.

    This is NOT the decision-maker — the LLM decides what to do next.
    This is only used for the progress display and confidence calculation.
    """
    if not evidence:
        return {f: 0.0 for f in REQUIRED_FIELDS}

    n = len(evidence)
    unique_sources = len({e.source_type for e in evidence})
    avg_relevance = sum(e.relevance_score for e in evidence) / n if n else 0.0

    # Base coverage scales with evidence count (diminishing returns)
    base = min(n / 10.0, 1.0)
    # Distribute across fields proportionally — all fields get some coverage
    coverage: dict[str, float] = {}
    for f in REQUIRED_FIELDS:
        coverage[f] = round(min(base * (0.5 + avg_relevance * 0.5), 1.0), 3)

    # Boost diversity
    diversity_bonus = min(unique_sources / 3.0, 1.0) * 0.1
    for f in REQUIRED_FIELDS:
        coverage[f] = round(min(coverage[f] + diversity_bonus, 1.0), 3)

    return coverage


def assess_coverage(
    evidence: list[EvidenceItem],
    config: dict,
) -> tuple[dict[str, float], float]:
    """Calculate coverage and confidence for progress display."""
    field_coverage = _estimate_field_coverage(evidence)
    conf_cfg = config.get("confidence", {})
    w_cov = float(conf_cfg.get("evidence_coverage_weight", 0.45))
    w_str = float(conf_cfg.get("evidence_strength_weight", 0.35))
    w_div = float(conf_cfg.get("source_diversity_weight", 0.20))

    evidence_coverage = sum(field_coverage.values()) / max(len(REQUIRED_FIELDS), 1)
    evidence_strength = (
        sum(e.relevance_score for e in evidence) / len(evidence) if evidence else 0.0
    )
    unique_types = {e.source_type for e in evidence}
    source_diversity = min(len(unique_types) / 3.0, 1.0)

    overall = evidence_coverage * w_cov + evidence_strength * w_str + source_diversity * w_div
    return field_coverage, round(overall, 4)
