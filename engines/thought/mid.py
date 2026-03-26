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

# Research phases — ordered like a real analyst would work
PHASES = [
    {
        "name": "PROFILE",
        "fields": ["company_profile", "industry_context", "scale_indicators"],
        "threshold": 0.5,
        "instructions": "Focus on understanding who this company is. What do they do, how big are they, what market are they in? Use GROUND (web search) — do NOT search the knowledge base yet.",
        "tool_guidance": "Use GROUND for company-specific facts. Do not use RAG in this phase — you need company context before searching past engagements.",
        "prefer": "ground",
    },
    {
        "name": "DISCOVER",
        "fields": ["business_processes", "pain_points"],
        "threshold": 0.5,
        "instructions": "Now dig into their operational challenges. What processes are manual? Where are the bottlenecks and inefficiencies? Use GROUND to find specific pain points.",
        "tool_guidance": "Use GROUND for operational details, challenges, and workflow information. RAG is acceptable if you need to check if a specific pain pattern matches past cases.",
        "prefer": "ground",
    },
    {
        "name": "MATCH",
        "fields": ["similar_wins"],
        "threshold": 0.4,
        "instructions": "You now understand the company and their pain points. Search our knowledge base for past engagements with similar patterns. Use SPECIFIC queries referencing the company's industry, size, and pain points — not generic searches.",
        "tool_guidance": "Use RAG to search past engagements. Reference specific pain points and industry context you discovered in earlier phases. GROUND is acceptable for follow-up validation.",
        "prefer": "rag",
    },
    {
        "name": "FILL",
        "fields": REQUIRED_FIELDS,
        "threshold": 0.5,
        "instructions": "Fill remaining gaps. Target the weakest fields. Use whichever tool is most appropriate. If tools cannot answer, ask the user.",
        "tool_guidance": "Use any tool. Prefer ASK_USER for information that only the company would know.",
        "prefer": "any",
    },
]


def detect_phase(field_coverage: dict[str, float]) -> dict:
    """Determine current research phase based on field coverage."""
    for phase in PHASES:
        target_fields = phase["fields"]
        avg_coverage = sum(field_coverage.get(f, 0.0) for f in target_fields) / max(len(target_fields), 1)
        if avg_coverage < phase["threshold"]:
            return phase
    return PHASES[-1]  # Default to FILL if all phases met


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
    briefing: str | None = None,
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

    # Initial fallback coverage estimate (used if LLM doesn't provide one)
    field_coverage = _estimate_field_coverage(evidence)
    overall = sum(field_coverage.values()) / max(len(REQUIRED_FIELDS), 1)
    contradictions: list[dict] = []

    # Detect research phase based on current coverage
    phase = detect_phase(field_coverage)

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
    prompt = prompt.replace("{evidence_summary}", briefing or _build_evidence_summary(evidence))
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
    prompt = prompt.replace("{phase_name}", phase["name"])
    prompt = prompt.replace("{phase_instructions}", phase["instructions"])
    prompt = prompt.replace("{phase_tool_guidance}", phase["tool_guidance"])
    # Convert escaped braces back for JSON example
    prompt = prompt.replace("{{", "{").replace("}}", "}")

    raw_text = grounder.reason(prompt, run_id)  # type: ignore[attr-defined]
    parsed = extract_json(raw_text)

    # Prefer LLM-provided field coverage over keyword fallback
    llm_fc = parsed.get("field_coverage")
    if llm_fc and isinstance(llm_fc, dict):
        field_coverage = {
            f: max(0.0, min(1.0, float(llm_fc.get(f, 0.0))))
            for f in REQUIRED_FIELDS
        }
        overall = sum(field_coverage.values()) / max(len(REQUIRED_FIELDS), 1)

    # Extract contradictions flagged by LLM
    llm_contradictions = parsed.get("contradictions")
    if llm_contradictions and isinstance(llm_contradictions, list):
        contradictions = llm_contradictions

    from services.trace import emit as _emit
    from core.events import EventType as _ET
    _emit(run_id, _ET.MID_GAP_DETECTED, {
        "react_raw_length": len(raw_text),
        "react_parsed_keys": list(parsed.keys()),
        "react_action": parsed.get("action", "NONE"),
        "react_thinking": str(parsed.get("thinking", ""))[:200],
        "phase": phase["name"],
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
        return field_coverage, overall, None, contradictions

    # Map action to gap
    action_map = {"GROUND": "ground", "RAG": "rag", "ASK_USER": "ask_user"}
    gap_action = action_map.get(action, "ask_user")

    # Phase enforcement: nudge LLM toward phase-preferred tool
    phase_prefer = phase.get("prefer", "any")
    if phase_prefer == "ground" and gap_action == "rag" and ground_remaining > 0:
        gap_action = "ground"  # Stay on web search during PROFILE/DISCOVER
    elif phase_prefer == "rag" and gap_action == "ground" and rag_remaining > 0:
        gap_action = "rag"  # Stay on KB search during MATCH

    # Budget enforcement: if chosen tool is exhausted, fall back
    if gap_action == "ground" and ground_remaining <= 0:
        gap_action = "rag" if rag_remaining > 0 else "ask_user"
    if gap_action == "rag" and rag_remaining <= 0:
        gap_action = "ground" if ground_remaining > 0 else "ask_user"

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
    return field_coverage, overall, gap, contradictions


_FIELD_SIGNALS: dict[str, list[str]] = {
    "company_profile": ["founded", "headquarter", "revenue", "employees", "ceo", "product", "platform", "company"],
    "industry_context": ["industry", "market", "sector", "competitor", "trend", "regulation", "compliance"],
    "business_processes": ["workflow", "process", "operations", "pipeline", "automat", "manual", "system"],
    "pain_points": ["pain", "challenge", "problem", "bottleneck", "friction", "cost", "slow", "error", "inefficien"],
    "similar_wins": ["engagement", "case", "implementation", "deploy", "pilot", "roi", "savings", "similar"],
    "scale_indicators": ["scale", "growth", "volume", "transaction", "headcount", "expand", "capacity"],
}


def _estimate_field_coverage(evidence: list[EvidenceItem]) -> dict[str, float]:
    """Field-specific coverage estimate based on evidence relevance signals.

    Scores each field independently by checking how much evidence relates
    to that field, weighted by relevance scores.
    """
    if not evidence:
        return {f: 0.0 for f in REQUIRED_FIELDS}

    unique_sources = len({e.source_type for e in evidence})
    diversity_bonus = min(unique_sources / 3.0, 1.0) * 0.08

    coverage: dict[str, float] = {}
    for field in REQUIRED_FIELDS:
        signals = _FIELD_SIGNALS.get(field, [])
        weighted_hits = 0.0
        for ev in evidence:
            text = f"{ev.title} {ev.snippet}".lower()
            hit_count = sum(1 for s in signals if s in text)
            if hit_count > 0:
                weighted_hits += ev.relevance_score * min(hit_count / 3.0, 1.0)
        raw = min(weighted_hits / 3.0, 1.0)
        coverage[field] = round(min(raw + diversity_bonus, 1.0), 3)

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
