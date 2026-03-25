"""Opportunity scoring — uses LLM evaluation scores when available.

Falls back to formula-based scoring only when LLM scores are missing.
"""
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
    """Compute four-dimension score plus composite using config weights.

    Prefers LLM-provided scores from the matching step.
    """
    scoring = config.get("scoring", {})
    w_roi = float(scoring.get("w_roi", 0.30))
    w_feas = float(scoring.get("w_feasibility", 0.30))
    w_ttv = float(scoring.get("w_ttv", 0.20))
    w_conf = float(scoring.get("w_confidence", 0.20))

    llm = match.llm_scores

    # Use LLM scores if available, otherwise fall back to ROI/engagement data
    feasibility = float(llm.get("feasibility", 0.0)) if llm else 0.0
    roi_score = float(llm.get("roi", 0.0)) if llm else 0.0
    ttv = float(llm.get("time_to_value", 0.0)) if llm else 0.0
    confidence = float(llm.get("confidence", 0.0)) if llm else 0.0

    # Fallback: if LLM scores are zero/missing, use formula
    if feasibility < 0.01:
        feasibility = 0.7 if match.matched_engagement_ids else 0.5
    if roi_score < 0.01 and roi_estimate:
        pct = roi_estimate.adjusted_value
        roi_score = 0.9 if pct >= 50 else (0.7 if pct >= 20 else 0.5)
    elif roi_score < 0.01:
        roi_score = 0.3
    if ttv < 0.01:
        timeline = roi_estimate.timeline_weeks if roi_estimate else match.template.typical_timeline_weeks
        ttv = 0.9 if timeline <= 8 else (0.7 if timeline <= 12 else (0.5 if timeline <= 16 else 0.3))
    if confidence < 0.01:
        if evidence_map and match.matched_evidence_ids:
            scores = [evidence_map[eid].relevance_score for eid in match.matched_evidence_ids if eid in evidence_map]
            confidence = sum(scores) / len(scores) if scores else 0.3
        else:
            confidence = 0.3

    composite = w_roi * roi_score + w_feas * feasibility + w_ttv * ttv + w_conf * confidence

    return {
        "feasibility": round(feasibility, 3),
        "roi": round(roi_score, 3),
        "time_to_value": round(ttv, 3),
        "confidence": round(confidence, 3),
        "composite": round(composite, 4),
    }
