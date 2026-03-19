"""Three-channel matching layer — bridges company signals to both solution libraries."""
from __future__ import annotations

import uuid

from orchestrator.schemas import MatchResult, ProvenMetrics

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
    a_l, b_l = a.lower(), b.lower()
    for cluster in _INDUSTRY_CLUSTERS:
        if any(a_l in c for c in cluster) and any(b_l in c for c in cluster):
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


def _score_library_a(record: dict, signals_industry: str, signals_scale: str,
                     maturity_label: str, company_signals: list[dict]) -> float:
    """Score a Library A record. Returns total 0.0-1.2."""
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

    maturity_score = _proximity_score(maturity_label, win_maturity, _MATURITY_LEVELS, 0.4)
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

    return industry_score + maturity_score + size_score + sector_bonus + signal_bonus


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

    return round(industry_score + signal_overlap + size_match, 3)
