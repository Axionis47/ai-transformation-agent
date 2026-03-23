from __future__ import annotations

from core.schemas import EvidenceItem
from engines.pitch.matcher import TemplateMatch
from engines.pitch.roi_model import ROIEstimate


def score_opportunity(
    match: TemplateMatch,
    roi_estimate: ROIEstimate | None,
    config: dict,
    evidence_map: dict[str, EvidenceItem] | None = None,
) -> dict:
    """Compute four-dimension score plus composite using config weights."""
    scoring = config.get("scoring", {})
    w_roi = float(scoring.get("w_roi", 0.30))
    w_feas = float(scoring.get("w_feasibility", 0.30))
    w_ttv = float(scoring.get("w_ttv", 0.20))
    w_conf = float(scoring.get("w_confidence", 0.20))

    # Feasibility: penalise for anti-signals, boost for same-industry engagement
    anti_count = len(match.anti_signal_hits)
    if anti_count == 0:
        feasibility = 0.9
    elif anti_count == 1:
        feasibility = 0.6
    else:
        feasibility = 0.3
    # Boost if matched engagements exist (same-industry check happens in tier classifier)
    if match.matched_engagement_ids:
        feasibility = min(1.0, feasibility + 0.1)

    # ROI score: map adjusted ROI value to 0-1 scale
    if roi_estimate is None:
        roi_score = 0.3
    else:
        pct = roi_estimate.adjusted_value
        if pct >= 50:
            roi_score = 0.9
        elif pct >= 20:
            roi_score = 0.7
        else:
            roi_score = 0.5

    # Time-to-value: based on timeline weeks
    timeline = roi_estimate.timeline_weeks if roi_estimate else match.template.typical_timeline_weeks
    if timeline <= 8:
        ttv = 0.9
    elif timeline <= 12:
        ttv = 0.7
    elif timeline <= 16:
        ttv = 0.5
    else:
        ttv = 0.3

    # Confidence: average relevance_score of matched evidence items
    if evidence_map and match.matched_evidence_ids:
        scores = [
            evidence_map[eid].relevance_score
            for eid in match.matched_evidence_ids
            if eid in evidence_map
        ]
        confidence = sum(scores) / len(scores) if scores else 0.3
    else:
        confidence = 0.3

    composite = (
        w_roi * roi_score
        + w_feas * feasibility
        + w_ttv * ttv
        + w_conf * confidence
    )

    return {
        "feasibility": round(feasibility, 3),
        "roi": round(roi_score, 3),
        "time_to_value": round(ttv, 3),
        "confidence": round(confidence, 3),
        "composite": round(composite, 4),
    }
