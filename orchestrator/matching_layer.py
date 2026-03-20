"""Three-channel matching layer — bridges company signals to both solution libraries."""
from __future__ import annotations

import re
import uuid

from orchestrator.schemas import MatchResult, ProvenMetrics

_STOPWORDS = {
    "the", "a", "is", "and", "of", "to", "in", "for", "that", "with",
    "was", "had", "not", "from", "this", "been", "have", "were", "are",
    "but", "they", "per",
}

_MATURITY_LEVELS = ["Beginner", "Developing", "Emerging", "Advanced", "Leading"]
_SIZE_LEVELS = ["startup", "mid-market", "enterprise"]

_INDUSTRY_CLUSTERS = [
    {"logistics", "manufacturing", "construction", "energy"},
    {"financial_services", "fintech", "insurance"},
    {"healthcare", "healthtech"},
    {"retail", "ecommerce"},
    {"professional_services", "real_estate", "proptech"},
]


def _industries_related(a: str, b: str) -> bool:
    """Check if two industry strings belong to the same cluster.

    Handles exact cluster members and compound labels like 'B2B logistics SaaS'.
    """
    a_l, b_l = a.lower(), b.lower()
    for cluster in _INDUSTRY_CLUSTERS:
        a_in = any(c in a_l or a_l in c for c in cluster)
        b_in = any(c in b_l or b_l in c for c in cluster)
        if a_in and b_in:
            return True
    return False


def _proximity_score(value: str, target: str, levels: list[str], max_score: float) -> float:
    vi = levels.index(value) if value in levels else -1
    ti = levels.index(target) if target in levels else -1
    if vi < 0 or ti < 0:
        return 0.0
    dist = abs(vi - ti)
    if dist == 0:
        return max_score
    if dist == 1:
        return max_score * 0.5
    return 0.0


def _map_confidence(raw: float, lo: float, hi: float, raw_min: float, raw_max: float) -> float:
    """Map raw score from [raw_min, raw_max] into [lo, hi]."""
    if raw_max <= raw_min:
        return lo
    t = (raw - raw_min) / (raw_max - raw_min)
    return round(min(hi, max(lo, lo + t * (hi - lo))), 3)


def _tokenize(text: str) -> set[str]:
    """Lowercase, split on non-word characters, remove stopwords."""
    tokens = re.split(r"\W+", text.lower())
    return {t for t in tokens if t and t not in _STOPWORDS}


def _pain_point_score(record: dict, company_signals: list[dict],
                      problem_key: str = "problem_statement") -> float:
    """Score keyword overlap between company pain points and a victory record.

    Extracts pain_point signal values from company_signals, tokenizes them,
    then computes overlap against the record's problem text and solution summary.
    Returns 0.0-0.15, scaled by overlap ratio.
    """
    pain_values = [
        s.get("value", "")
        for s in company_signals
        if s.get("type") == "pain_point" and s.get("value")
    ]
    if not pain_values:
        return 0.0

    pain_tokens = _tokenize(" ".join(pain_values))
    if not pain_tokens:
        return 0.0

    problem_text = record.get(problem_key, "") or ""
    solution_text = record.get("solution_summary", "") or ""
    record_tokens = _tokenize(f"{problem_text} {solution_text}")

    if not record_tokens:
        return 0.0

    overlap = len(pain_tokens & record_tokens)
    ratio = overlap / len(pain_tokens)
    return round(min(0.15, 0.15 * ratio), 4)


def _tech_stack_score(record: dict, company_signals: list[dict]) -> float:
    """Score tech stack overlap between company signals and a victory record.

    Extracts tech_stack signal values from company_signals, flattens the
    record's tech_stack dict (infrastructure, data_sources,
    client_systems_integrated lists + ml_approach string), tokenizes both
    sides, and returns 0.0-0.15 scaled by overlap ratio.
    """
    tech_values = [
        s.get("value", "")
        for s in company_signals
        if s.get("type") == "tech_stack" and s.get("value")
    ]
    if not tech_values:
        return 0.0

    company_tokens = _tokenize(" ".join(tech_values))
    if not company_tokens:
        return 0.0

    tech = record.get("tech_stack", {})
    if not isinstance(tech, dict):
        return 0.0

    record_parts: list[str] = []
    for key in ("infrastructure", "data_sources", "client_systems_integrated"):
        val = tech.get(key, [])
        if isinstance(val, list):
            record_parts.extend(str(v) for v in val)
    ml = tech.get("ml_approach", "")
    if ml:
        record_parts.append(str(ml))

    record_tokens = _tokenize(" ".join(record_parts))
    if not record_tokens:
        return 0.0

    overlap = len(company_tokens & record_tokens)
    ratio = overlap / len(company_tokens)
    return round(min(0.15, 0.15 * ratio), 4)


def _score_library_a(record: dict, signals_industry: str, signals_scale: str,
                     maturity_label: str, company_signals: list[dict]) -> float:
    """Score a Library A record. Returns total 0.0-1.50 (tech + pain bonuses up to 0.30)."""
    win_industry = record.get("industry", "")
    win_size = record.get("size_label", "")
    if not win_size:
        profile = record.get("company_profile", {})
        if isinstance(profile, dict):
            win_size = profile.get("size_label", "")
    win_maturity = record.get("maturity_at_engagement", "")

    if signals_industry.lower() == win_industry.lower():
        industry_score = 0.4
    elif _industries_related(signals_industry, win_industry):
        industry_score = 0.2
    else:
        industry_score = 0.0

    if win_maturity:
        maturity_score = _proximity_score(maturity_label, win_maturity, _MATURITY_LEVELS, 0.4)
    else:
        maturity_score = 0.15  # neutral score when field is missing
    size_score = _proximity_score(signals_scale, win_size, _SIZE_LEVELS, 0.2)

    company_process_values = {
        s.get("value", "").lower()
        for s in company_signals
        if s.get("type") in ("process_signal", "ops_signal")
    }
    sector_tags = {t.lower() for t in record.get("sector_tags", [])}
    sector_bonus = 0.1 if company_process_values & sector_tags else 0.0

    company_signal_types = {s.get("type", "") for s in company_signals}
    applicable = set(record.get("applicable_signals", []))
    signal_bonus = 0.1 if applicable & company_signal_types else 0.0

    pain_score = _pain_point_score(record, company_signals)
    tech_score = _tech_stack_score(record, company_signals)

    return industry_score + maturity_score + size_score + sector_bonus + signal_bonus + pain_score + tech_score


def _score_library_b(record: dict, signals_industry: str, signals_scale: str,
                     company_signals: list[dict]) -> float:
    """Score a Library B record. Returns total 0.0-1.0."""
    case_industry = record.get("industry", "")
    if signals_industry.lower() == case_industry.lower():
        industry_score = 0.4
    elif _industries_related(signals_industry, case_industry):
        industry_score = 0.2
    else:
        industry_score = 0.0

    company_signal_types = {s.get("type", "") for s in company_signals}
    applicable = set(record.get("applicable_signals", []))
    total_applicable = len(applicable) if applicable else 1
    overlap = len(applicable & company_signal_types)
    signal_overlap = min(0.4, 0.4 * (overlap / total_applicable))

    company_type = ""
    if isinstance(record.get("company_profile"), dict):
        company_type = record["company_profile"].get("company_type", "")
    size_match = 0.2 if signals_scale.lower() == company_type.lower() else 0.0

    # Library B records may carry a problem_statement field
    pain_score = 0.0
    if record.get("problem_statement"):
        pain_score = _pain_point_score(record, company_signals)

    tech_score = _tech_stack_score(record, company_signals)

    return round(industry_score + signal_overlap + size_match + pain_score + tech_score, 3)


def _build_delivered(record: dict, score: float, composite_score: float) -> MatchResult:
    results = record.get("results", {})
    pm_dict = results.get("primary_metric", {}) if isinstance(results, dict) else {}
    pm = ProvenMetrics(
        primary_label=pm_dict.get("label", ""),
        primary_value=pm_dict.get("value", ""),
        measurement_period=results.get("measurement_period", "") if isinstance(results, dict) else "",
    )
    profile = record.get("company_profile", {}) if isinstance(record.get("company_profile"), dict) else {}
    win_maturity = record.get("maturity_at_engagement", "")
    win_float = _MATURITY_LEVELS.index(win_maturity) + 1.0 if win_maturity in _MATURITY_LEVELS else 0.0
    gap = abs(composite_score - win_float)
    gap_text: str | None = None
    template = record.get("gap_analysis_template", "")
    if record.get("industry_benchmark") and template:
        gap_text = f"Industry benchmark: {record['industry_benchmark']}. Maturity gap: {gap:.1f} points."
        if record.get("success_threshold"):
            gap_text += f" {record['success_threshold']}"
        gap_text += f" {template.format(gap=f'{gap:.1f}')}"
    tech = record.get("tech_stack", {})
    return MatchResult(
        result_id=f"mr-{uuid.uuid4().hex[:6]}",
        source_library="tenex_delivered",
        match_tier="DELIVERED",
        confidence=_map_confidence(score, 0.80, 0.95, 0.60, 1.2),
        similarity_score=round(score, 3),
        source_id=record.get("id", ""),
        source_title=record.get("engagement_title", ""),
        source_industry=record.get("industry", ""),
        relevance_note=f"Industry: {record.get('industry','')}, Maturity: {win_maturity}, Score: {score:.2f}",
        proven_metrics=pm,
        client_profile_summary=(
            f"{profile.get('size_label','')} {record.get('industry','')} company, "
            f"{profile.get('size_employees','')} employees, {profile.get('geography','')}"
        ).strip(", "),
        engagement_duration=record.get("engagement_details", {}).get("duration_months")
        if isinstance(record.get("engagement_details"), dict) else None,
        tech_approach=tech.get("ml_approach", "") if isinstance(tech, dict) else "",
        gap_analysis=gap_text,
    )


def _build_adaptation(record: dict, score: float, composite_score: float) -> MatchResult:
    win_maturity = record.get("maturity_at_engagement", "")
    win_float = _MATURITY_LEVELS.index(win_maturity) + 1.0 if win_maturity in _MATURITY_LEVELS else 0.0
    gap_from_base = round(abs(composite_score - win_float), 2)
    results = record.get("results", {})
    pm = results.get("primary_metric", {}) if isinstance(results, dict) else {}
    base_roi = f"{pm.get('label', '')}: {pm.get('value', '')}".strip(": ")
    tech = record.get("tech_stack", {})
    approach = tech.get("ml_approach", "ML model") if isinstance(tech, dict) else "ML model"
    return MatchResult(
        result_id=f"mr-{uuid.uuid4().hex[:6]}",
        source_library="tenex_delivered",
        match_tier="ADAPTATION",
        confidence=_map_confidence(score, 0.55, 0.79, 0.30, 0.59),
        similarity_score=round(score, 3),
        source_id=record.get("id", ""),
        source_title=record.get("engagement_title", ""),
        source_industry=record.get("industry", ""),
        relevance_note=f"Adjacent match — industry: {record.get('industry','')}, score: {score:.2f}",
        base_solution_id=record.get("id", ""),
        adaptation_notes=(
            f"Base: {record.get('engagement_title', '')}. "
            f"Core approach ({approach}) remains applicable. "
            "Industry adaptation required for target sector."
        ),
        gap_from_base=gap_from_base,
        estimated_scope_delta="20-30% more effort due to domain differences",
        adjusted_roi_range=f"Base: {base_roi} -- adapted estimate: 60-80% of base ROI",
    )


def _build_ambitious(record: dict, score: float) -> MatchResult:
    outcomes = record.get("reported_outcomes", {})
    headline = outcomes.get("headline_metric", "") if isinstance(outcomes, dict) else ""
    source = outcomes.get("source", "") if isinstance(outcomes, dict) else ""
    profile = record.get("company_profile", {})
    company_name = profile.get("company_name", "") if isinstance(profile, dict) else ""
    ai_app = record.get("ai_application", {})
    dep_scale = ai_app.get("deployment_scale", "") if isinstance(ai_app, dict) else ""
    return MatchResult(
        result_id=f"mr-{uuid.uuid4().hex[:6]}",
        source_library="industry_cases",
        match_tier="AMBITIOUS",
        confidence=_map_confidence(score, 0.40, 0.65, 0.30, 1.0),
        similarity_score=score,
        source_id=record.get("id", ""),
        source_title=record.get("case_title", ""),
        source_industry=record.get("industry", ""),
        relevance_note=f"Industry case — {record.get('industry', '')}, score: {score:.2f}",
        industry_examples=[company_name] if company_name else [],
        source_citations=[source] if source else [],
        deployment_scale=dep_scale,
        implementation_maturity="mainstream" if score >= 0.6 else "early adopter",
        experimental_roi_range=f"{headline} -- industry estimate" if headline else "",
    )


def match(
    signals: dict,
    maturity: dict,
    delivered_results: list[dict],
    industry_results: list[dict],
) -> dict[str, list[MatchResult]]:
    """Return three-tier matching output from two solution libraries.

    DELIVERED (confidence 0.80-0.95): Library A records with score >= 0.60.
    ADAPTATION (confidence 0.55-0.79): Library A records with score 0.30-0.59.
    AMBITIOUS (confidence 0.40-0.65): Library B records with score >= 0.20.
    A Library A record appears in at most one track.
    """
    industry = signals.get("industry", "unknown")
    scale = signals.get("scale", "unknown")
    maturity_label = maturity.get("composite_label", "")
    composite_score = float(maturity.get("composite_score", 0.0))
    company_signals: list[dict] = signals.get("signals", [])

    delivered: list[MatchResult] = []
    adaptation: list[MatchResult] = []
    for record in delivered_results:
        score = _score_library_a(record, industry, scale, maturity_label, company_signals)
        if score >= 0.60:
            delivered.append(_build_delivered(record, score, composite_score))
        elif score >= 0.30:
            adaptation.append(_build_adaptation(record, score, composite_score))

    delivered.sort(key=lambda r: -r.similarity_score)
    adaptation.sort(key=lambda r: -r.similarity_score)

    ambitious: list[MatchResult] = []
    for record in industry_results:
        score = _score_library_b(record, industry, scale, company_signals)
        if score >= 0.20:
            ambitious.append(_build_ambitious(record, score))
    ambitious.sort(key=lambda r: -r.similarity_score)

    return {"delivered": delivered, "adaptation": adaptation, "ambitious": ambitious}
