from __future__ import annotations

from dataclasses import dataclass, field

SIZE_BANDS = ["50-100", "100-200", "200-500", "500-2000", "2000+"]


def _band_index(band: str | None) -> int | None:
    if band is None:
        return None
    try:
        return SIZE_BANDS.index(band)
    except ValueError:
        return None


def _size_factor(company_band: str | None, eng_band: str | None) -> float:
    ci = _band_index(company_band)
    ei = _band_index(eng_band)
    if ci is None or ei is None:
        return 1.0
    diff = abs(ci - ei)
    if diff == 0:
        return 1.0
    if diff == 1:
        return 0.6 if ci < ei else 1.3
    return 0.4


def _industry_factor(company_industry: str, eng_industry: str) -> float:
    if company_industry == eng_industry:
        return 1.0
    adjacent = {
        frozenset({"healthcare", "financial_services"}),
        frozenset({"logistics", "manufacturing"}),
        frozenset({"professional_services", "financial_services"}),
    }
    pair = frozenset({company_industry, eng_industry})
    if pair in adjacent:
        return 0.8
    return 0.6


@dataclass
class ROIEstimate:
    primary_metric: str
    base_value: float
    adjusted_value: float
    size_factor: float
    industry_factor: float
    source_engagement_id: str
    timeline_weeks: int
    assumptions: dict
    sensitivity: dict = field(default_factory=dict)


def _best_metric(measured_impact: dict) -> tuple[str, float]:
    """Pick metric with highest numeric value as primary ROI driver."""
    best_key, best_val = "", 0.0
    for k, v in measured_impact.items():
        try:
            f = float(v)
            if f > best_val:
                best_val = f
                best_key = k
        except (TypeError, ValueError):
            continue
    return best_key, best_val


def translate_roi(
    matched_engagement_ids: list[str],
    company_size_band: str | None,
    company_industry: str,
    engagement_lookup: dict[str, dict],
) -> ROIEstimate | None:
    """Translate past engagement ROI to this company using scaling factors."""
    if not matched_engagement_ids:
        return None

    best_eng: dict | None = None
    best_eng_id: str = ""
    best_val: float = -1.0

    for eng_id in matched_engagement_ids:
        eng = engagement_lookup.get(eng_id)
        if eng is None:
            continue
        _, val = _best_metric(eng.get("measured_impact", {}))
        if val > best_val:
            best_val = val
            best_eng = eng
            best_eng_id = eng_id

    if best_eng is None:
        return None

    metric_key, base_value = _best_metric(best_eng.get("measured_impact", {}))
    if not metric_key:
        return None

    eng_band = best_eng.get("company_size_band")
    eng_industry = best_eng.get("industry", "")

    sf = _size_factor(company_size_band, eng_band)
    ind_f = _industry_factor(company_industry, eng_industry)
    adjusted = round(base_value * sf * ind_f, 2)

    # Sensitivity: vary each factor +/- 20%
    sensitivity = {
        "size_factor_high": round(base_value * min(sf * 1.2, 1.5) * ind_f, 2),
        "size_factor_low": round(base_value * max(sf * 0.8, 0.1) * ind_f, 2),
        "industry_factor_high": round(base_value * sf * min(ind_f * 1.2, 1.0), 2),
        "industry_factor_low": round(base_value * sf * max(ind_f * 0.8, 0.1), 2),
    }

    return ROIEstimate(
        primary_metric=metric_key,
        base_value=base_value,
        adjusted_value=adjusted,
        size_factor=sf,
        industry_factor=ind_f,
        source_engagement_id=best_eng_id,
        timeline_weeks=int(best_eng.get("timeline_weeks", 12)),
        assumptions={
            "company_size_band": company_size_band,
            "engagement_size_band": eng_band,
            "company_industry": company_industry,
            "engagement_industry": eng_industry,
        },
        sensitivity=sensitivity,
    )
