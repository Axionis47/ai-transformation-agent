"""Three-channel matching layer — bridges company signals to both solution libraries."""
from __future__ import annotations

import re
import uuid

from orchestrator.schemas import ConfidenceBreakdown, LessonsLearned, MatchResult, ProvenMetrics

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


def _score_library_a(
    record: dict, signals_industry: str, signals_scale: str,
    maturity_label: str, company_signals: list[dict],
) -> tuple[float, dict]:
    """Score a Library A record. Returns (total, components) where total is 0.0-1.50."""
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

    _sector_signal_types = {
        "process_signal", "ops_signal",
        "pain_point", "hiring_signal", "intent_signal", "industry_hint",
    }
    company_sector_values = [
        s.get("value", "").lower().replace("_", " ")
        for s in company_signals
        if s.get("type") in _sector_signal_types and s.get("value")
    ]
    sector_tags_norm = [t.lower().replace("_", " ") for t in record.get("sector_tags", [])]
    sector_bonus = 0.0
    for tag in sector_tags_norm:
        for val in company_sector_values:
            if tag in val or val in tag:
                sector_bonus = 0.1
                break
        if sector_bonus:
            break

    company_signal_types = {s.get("type", "") for s in company_signals}
    applicable = set(record.get("applicable_signals", []))
    signal_bonus = 0.1 if applicable & company_signal_types else 0.0

    pain_score = _pain_point_score(record, company_signals)
    tech_score = _tech_stack_score(record, company_signals)

    total = industry_score + maturity_score + size_score + sector_bonus + signal_bonus + pain_score + tech_score
    components = {
        "industry": industry_score, "maturity": maturity_score,
        "size": size_score, "pain": pain_score, "tech": tech_score,
    }
    return total, components


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


def _evidence_ceiling(company_signals: list[dict]) -> str:
    """Determine evidence ceiling from signal sources."""
    sources = {s.get("source", "") for s in company_signals}
    if "user_hint" in sources:
        return "url_plus_hints"
    return "url_only"


def _build_confidence_breakdown(
    industry_score: float,
    maturity_score: float,
    size_score: float,
    pain_score: float,
    tech_score: float,
    total: float,
    company_signals: list[dict],
) -> ConfidenceBreakdown:
    ceiling = _evidence_ceiling(company_signals)
    mapped = _map_confidence(total, 0.80, 0.95, 0.60, 1.2)
    parts = [
        f"industry={industry_score:.2f}",
        f"maturity={maturity_score:.2f}",
        f"scale={size_score:.2f}",
        f"pain={pain_score:.2f}",
        f"tech={tech_score:.2f}",
    ]
    return ConfidenceBreakdown(
        industry_match=round(industry_score / 0.4, 3),
        pain_point_match=round(min(1.0, pain_score / 0.15), 3),
        tech_feasibility=round(min(1.0, tech_score / 0.15), 3),
        scale_match=round(size_score / 0.2, 3),
        maturity_fit=round(maturity_score / 0.4, 3),
        evidence_depth=round(min(1.0, total / 1.2), 3),
        evidence_ceiling=ceiling,
        overall=mapped,
        explanation="; ".join(parts),
    )


def _assess_transferability(record: dict, company_signals: list[dict]) -> dict:
    """Compare victory requirements against company capabilities.

    Returns:
      transfers: list[str] — specific things that transfer (with signal refs)
      gaps: list[str] — specific things missing or needing build
      problem_match: float 0-1 — how well problems align
      tech_match: float 0-1 — infrastructure readiness
      data_match: float 0-1 — data availability
      scope_delta_pct: int — estimated extra effort %
      roi_discount: float — discount factor (0.5 = 50% of base ROI)
    """
    tech = record.get("tech_stack", {}) if isinstance(record.get("tech_stack"), dict) else {}
    infra_list = tech.get("infrastructure", []) if isinstance(tech.get("infrastructure"), list) else []
    data_list = tech.get("data_sources", []) if isinstance(tech.get("data_sources"), list) else []

    company_tech_signals = [
        s for s in company_signals
        if s.get("type") in ("tech_stack",) and s.get("value")
    ]
    company_data_signals = [
        s for s in company_signals
        if s.get("type") in ("data_signal", "tech_stack") and s.get("value")
    ]
    company_pain_signals = [
        s for s in company_signals
        if s.get("type") in ("pain_point", "process_signal") and s.get("value")
    ]

    # Problem match: pain + process signals vs victory problem text
    problem_match = 0.0
    if company_pain_signals:
        pain_tokens = _tokenize(" ".join(s.get("value", "") for s in company_pain_signals))
        prob_tokens = _tokenize(
            f"{record.get('problem_statement', '')} {record.get('solution_summary', '')}"
        )
        if pain_tokens and prob_tokens:
            overlap = len(pain_tokens & prob_tokens)
            problem_match = min(1.0, overlap / max(1, len(pain_tokens)))

    # Tech match: compare company tech signals against victory infra requirements
    transfers: list[str] = []
    gaps: list[str] = []
    tech_match = 0.0
    if infra_list:
        matched = 0
        company_tech_tokens = _tokenize(
            " ".join(s.get("value", "") for s in company_tech_signals)
        ) if company_tech_signals else set()
        for item in infra_list:
            item_tokens = _tokenize(str(item))
            sig_id = next(
                (s.get("signal_id") or "sig-unknown" for s in company_tech_signals
                 if item_tokens & _tokenize(s.get("value", ""))),
                None,
            )
            if item_tokens & company_tech_tokens:
                matched += 1
                ref = f"({sig_id})" if sig_id else ""
                transfers.append(
                    f"Company has matching infrastructure for '{item}' {ref}".strip()
                )
            else:
                gaps.append(
                    f"No signal detected for required infrastructure: '{item}'"
                )
        tech_match = matched / len(infra_list)

    # Data match: company data signals vs victory data source requirements
    data_match = 0.0
    if data_list:
        matched_d = 0
        company_data_tokens = _tokenize(
            " ".join(s.get("value", "") for s in company_data_signals)
        ) if company_data_signals else set()
        for item in data_list:
            item_tokens = _tokenize(str(item))
            if item_tokens & company_data_tokens:
                matched_d += 1
                sig_id = next(
                    (s.get("signal_id") or "sig-unknown" for s in company_data_signals
                     if item_tokens & _tokenize(s.get("value", ""))),
                    None,
                )
                ref = f"({sig_id})" if sig_id else ""
                transfers.append(
                    f"Company data available for '{item}' {ref}".strip()
                )
            else:
                gaps.append(
                    f"No signal detected for required data source: '{item}'"
                )
        data_match = matched_d / len(data_list)

    # scope_delta_pct: base 0, +15% per gap, cap at 80%
    scope_delta_pct = min(80, len(gaps) * 15)

    # roi_discount: weighted sum, clamped to [0.3, 0.9]
    roi_discount = 0.4 + 0.2 * problem_match + 0.2 * tech_match + 0.2 * data_match
    roi_discount = round(max(0.3, min(0.9, roi_discount)), 3)

    return {
        "transfers": transfers,
        "gaps": gaps,
        "problem_match": round(problem_match, 3),
        "tech_match": round(tech_match, 3),
        "data_match": round(data_match, 3),
        "scope_delta_pct": scope_delta_pct,
        "roi_discount": roi_discount,
    }


def _build_delivered(record: dict, score: float, composite_score: float,
                     component_scores: dict | None = None,
                     company_signals: list[dict] | None = None) -> MatchResult:
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
    raw_ll = record.get("lessons_learned")
    ll: LessonsLearned | None = None
    if isinstance(raw_ll, dict) and raw_ll:
        ll = LessonsLearned(
            primary_challenge=raw_ll.get("primary_challenge", ""),
            risk_factors=raw_ll.get("risk_factors", []),
            timeline_reality=raw_ll.get("timeline_reality", ""),
            what_we_would_do_differently=raw_ll.get("what_we_would_do_differently", ""),
        )

    # Run transferability to verify prerequisites and enrich relevance note
    sigs = company_signals or []
    ta = _assess_transferability(record, sigs)
    prereq_parts = []
    if ta["gaps"]:
        prereq_parts.append(f"Prerequisites needed: {'; '.join(ta['gaps'][:2])}")
    if ta["transfers"]:
        prereq_parts.append(f"Confirmed ready: {'; '.join(ta['transfers'][:2])}")
    prereq_note = (" | " + " | ".join(prereq_parts)) if prereq_parts else ""
    relevance_note = (
        f"Industry: {record.get('industry','')}, Maturity: {win_maturity}, "
        f"Score: {score:.2f}{prereq_note}"
    )

    breakdown: ConfidenceBreakdown | None = None
    if component_scores is not None:
        cb = _build_confidence_breakdown(
            industry_score=component_scores.get("industry", 0.0),
            maturity_score=component_scores.get("maturity", 0.0),
            size_score=component_scores.get("size", 0.0),
            pain_score=component_scores.get("pain", 0.0),
            tech_score=component_scores.get("tech", 0.0),
            total=score,
            company_signals=sigs,
        )
        ta_note = (
            f"problem_match={ta['problem_match']:.2f}; "
            f"tech_match={ta['tech_match']:.2f}; "
            f"data_match={ta['data_match']:.2f}"
        )
        breakdown = cb.model_copy(update={"explanation": f"{cb.explanation}; {ta_note}"})

    return MatchResult(
        result_id=f"mr-{uuid.uuid4().hex[:6]}",
        source_library="tenex_delivered",
        match_tier="DELIVERED",
        confidence=_map_confidence(score, 0.80, 0.95, 0.60, 1.2),
        similarity_score=round(score, 3),
        source_id=record.get("id", ""),
        source_title=record.get("engagement_title", ""),
        source_industry=record.get("industry", ""),
        relevance_note=relevance_note,
        proven_metrics=pm,
        client_profile_summary=(
            f"{profile.get('size_label','')} {record.get('industry','')} company, "
            f"{profile.get('size_employees','')} employees, {profile.get('geography','')}"
        ).strip(", "),
        engagement_duration=record.get("engagement_details", {}).get("duration_months")
        if isinstance(record.get("engagement_details"), dict) else None,
        tech_approach=tech.get("ml_approach", "") if isinstance(tech, dict) else "",
        gap_analysis=gap_text,
        lessons_learned=ll,
        confidence_breakdown=breakdown,
    )


def _build_adaptation(record: dict, score: float, composite_score: float,
                      company_signals: list[dict] | None = None) -> MatchResult:
    win_maturity = record.get("maturity_at_engagement", "")
    win_float = _MATURITY_LEVELS.index(win_maturity) + 1.0 if win_maturity in _MATURITY_LEVELS else 0.0
    gap_from_base = round(abs(composite_score - win_float), 2)
    results = record.get("results", {})
    pm = results.get("primary_metric", {}) if isinstance(results, dict) else {}
    base_label = pm.get("label", "")
    base_value = pm.get("value", "")
    base_roi = f"{base_label}: {base_value}".strip(": ")
    tech = record.get("tech_stack", {})
    approach = tech.get("ml_approach", "ML model") if isinstance(tech, dict) else "ML model"

    sigs = company_signals or []
    ta = _assess_transferability(record, sigs)

    # Build specific adaptation_notes from computed transfers/gaps
    if ta["transfers"] or ta["gaps"]:
        transfer_str = "; ".join(ta["transfers"]) if ta["transfers"] else "none detected"
        gap_str = "; ".join(ta["gaps"]) if ta["gaps"] else "none"
        direct = "directly" if ta["tech_match"] >= 0.5 and ta["data_match"] >= 0.5 else "partially"
        notes = (
            f"Transfers: {transfer_str}. "
            f"Gaps: {gap_str}. "
            f"Core approach ({approach}) is {direct} applicable."
        )
    else:
        notes = (
            f"Base: {record.get('engagement_title', '')}. "
            f"Core approach ({approach}) may be applicable. "
            "Insufficient signals to confirm direct fit — further discovery required."
        )

    # Build specific scope delta from gap count
    gap_count = len(ta["gaps"])
    if gap_count == 0:
        scope_delta = "Minimal additional effort — company infrastructure aligns with base solution"
    else:
        gap_list = "; ".join(ta["gaps"][:3])
        scope_delta = (
            f"{ta['scope_delta_pct']}% additional effort — "
            f"{gap_count} gap(s) to close: {gap_list}"
        )

    # Build specific ROI range from roi_discount and base metric.
    # Use only the first standalone percentage to avoid garbled values like
    # "200 descriptions/day (13x increase)" parsing to "200.13".
    pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', base_value)
    if pct_match:
        numeric_val = float(pct_match.group(1))
        lo = max(1, int(ta["roi_discount"] * numeric_val * 0.8))
        hi = int(ta["roi_discount"] * numeric_val * 1.2)
        adj_roi = f"{lo}-{hi}% {base_label}" if base_label else f"{lo}-{hi}% of base metric"
    else:
        pct = int(ta["roi_discount"] * 100)
        adj_roi = f"~{pct}% of base ROI ({base_roi})" if base_roi else f"~{pct}% of base ROI"

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
        adaptation_notes=notes,
        gap_from_base=gap_from_base,
        estimated_scope_delta=scope_delta,
        adjusted_roi_range=adj_roi,
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
        score, components = _score_library_a(record, industry, scale, maturity_label, company_signals)
        if score >= 0.60:
            delivered.append(_build_delivered(record, score, composite_score,
                                              component_scores=components,
                                              company_signals=company_signals))
        elif score >= 0.30:
            adaptation.append(_build_adaptation(record, score, composite_score,
                                                company_signals=company_signals))

    delivered.sort(key=lambda r: -r.similarity_score)
    adaptation.sort(key=lambda r: -r.similarity_score)

    ambitious: list[MatchResult] = []
    for record in industry_results:
        score = _score_library_b(record, industry, scale, company_signals)
        if score >= 0.20:
            ambitious.append(_build_ambitious(record, score))
    ambitious.sort(key=lambda r: -r.similarity_score)

    return {"delivered": delivered, "adaptation": adaptation, "ambitious": ambitious}
