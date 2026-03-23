from __future__ import annotations

from dataclasses import dataclass

from core.schemas import BudgetState, EvidenceItem

REQUIRED_FIELDS = [
    "company_profile",
    "industry_context",
    "business_processes",
    "pain_points",
    "similar_wins",
    "scale_indicators",
]

FIELD_KEYWORDS: dict[str, list[str]] = {
    "company_profile": ["company", "founded", "provides", "offers", "products", "services", "headquartered"],
    "industry_context": ["industry", "market", "sector", "trend", "competitive", "regulation"],
    "business_processes": ["process", "workflow", "operations", "pipeline", "manual", "system"],
    "pain_points": ["challenge", "problem", "issue", "bottleneck", "inefficient", "costly"],
    "similar_wins": ["engagement", "implementation", "automation", "deployed", "roi", "reduction"],
    "scale_indicators": ["employees", "revenue", "customers", "volume", "tickets", "transactions"],
}

FIELD_TOOL_MAP: dict[str, str] = {
    "company_profile": "ground",
    "industry_context": "ground",
    "business_processes": "ground",
    "pain_points": "ground",
    "similar_wins": "rag",
    "scale_indicators": "ask_user",
}

_GROUND_FALLBACK: dict[str, str] = {
    "industry_context": "rag",
}


@dataclass
class MIDGap:
    field: str
    coverage: float
    action: str


def assess_coverage(
    evidence: list[EvidenceItem],
    config: dict,
) -> tuple[dict[str, float], float]:
    """Calculate per-field coverage and overall confidence score."""
    field_coverage: dict[str, float] = {}
    for field in REQUIRED_FIELDS:
        keywords = FIELD_KEYWORDS[field]
        match_count = 0
        for item in evidence:
            text = (item.snippet + " " + item.title).lower()
            if any(kw in text for kw in keywords):
                match_count += 1
        if match_count == 0:
            field_coverage[field] = 0.0
        elif match_count == 1:
            field_coverage[field] = 0.5
        else:
            field_coverage[field] = 1.0

    conf_cfg = config.get("confidence", {})
    w_cov = float(conf_cfg.get("evidence_coverage_weight", 0.45))
    w_str = float(conf_cfg.get("evidence_strength_weight", 0.35))
    w_div = float(conf_cfg.get("source_diversity_weight", 0.20))

    evidence_coverage = (sum(field_coverage.values()) / len(REQUIRED_FIELDS)) if REQUIRED_FIELDS else 0.0
    evidence_strength = (
        sum(e.relevance_score for e in evidence) / len(evidence) if evidence else 0.0
    )
    unique_types = {e.source_type for e in evidence}
    source_diversity = min(len(unique_types) / 3.0, 1.0)

    overall = evidence_coverage * w_cov + evidence_strength * w_str + source_diversity * w_div
    return field_coverage, round(overall, 4)


def detect_gap(
    evidence: list[EvidenceItem],
    budget_state: BudgetState,
    config: dict,
) -> MIDGap | None:
    """Find biggest coverage gap and recommend an action. Returns None if all fields covered."""
    field_coverage, _ = assess_coverage(evidence, config)
    budgets = config.get("budgets", config)
    search_budget = int(budgets.get("external_search_query_budget", 5))
    rag_budget = int(budgets.get("rag_query_budget", 8))
    ground_exhausted = budget_state.external_search_queries_used >= search_budget
    rag_exhausted = budget_state.rag_queries_used >= rag_budget

    sorted_fields = sorted(REQUIRED_FIELDS, key=lambda f: field_coverage.get(f, 0.0))
    for field in sorted_fields:
        if field_coverage.get(field, 0.0) >= 0.5:
            continue
        preferred = FIELD_TOOL_MAP[field]
        if preferred == "ground" and not ground_exhausted:
            return MIDGap(field=field, coverage=field_coverage[field], action="ground")
        if preferred == "ground" and ground_exhausted:
            fallback = _GROUND_FALLBACK.get(field)
            if fallback == "rag" and not rag_exhausted:
                return MIDGap(field=field, coverage=field_coverage[field], action="rag")
            return MIDGap(field=field, coverage=field_coverage[field], action="ask_user")
        if preferred == "rag" and not rag_exhausted:
            return MIDGap(field=field, coverage=field_coverage[field], action="rag")
        if preferred == "rag" and rag_exhausted:
            return MIDGap(field=field, coverage=field_coverage[field], action="ask_user")
        return MIDGap(field=field, coverage=field_coverage[field], action="ask_user")
    return None
