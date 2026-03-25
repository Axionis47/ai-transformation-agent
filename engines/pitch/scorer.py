"""Opportunity scoring — uses LLM evaluation scores when available.

When LLM scores are missing and no data supports a computed score,
marks the dimension as None and flags data_sufficiency accordingly.
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
    Falls back to evidence-derived scores when possible.
    Marks dimensions as None when no data supports a score.
    """
    scoring = config.get("scoring", {})
    weights = {
        "roi": float(scoring.get("w_roi", 0.30)),
        "feasibility": float(scoring.get("w_feasibility", 0.30)),
        "time_to_value": float(scoring.get("w_ttv", 0.20)),
        "confidence": float(scoring.get("w_confidence", 0.20)),
    }

    llm = match.llm_scores

    # Extract LLM scores (0.0 means missing)
    feasibility = float(llm.get("feasibility", 0.0)) if llm else 0.0
    roi_score = float(llm.get("roi", 0.0)) if llm else 0.0
    ttv = float(llm.get("time_to_value", 0.0)) if llm else 0.0
    confidence = float(llm.get("confidence", 0.0)) if llm else 0.0

    # Evidence-derived fallbacks only when data exists
    if feasibility < 0.01 and match.matched_engagement_ids:
        feasibility = 0.7
    if roi_score < 0.01 and roi_estimate:
        pct = roi_estimate.adjusted_value
        roi_score = 0.9 if pct >= 50 else (0.7 if pct >= 20 else 0.5)
    if ttv < 0.01:
        timeline = roi_estimate.timeline_weeks if roi_estimate else match.template.typical_timeline_weeks
        if timeline:
            ttv = 0.9 if timeline <= 8 else (0.7 if timeline <= 12 else (0.5 if timeline <= 16 else 0.3))
    if confidence < 0.01 and evidence_map and match.matched_evidence_ids:
        scores = [evidence_map[eid].relevance_score for eid in match.matched_evidence_ids if eid in evidence_map]
        if scores:
            confidence = sum(scores) / len(scores)

    # Build result, marking insufficient dimensions as None
    dims = {"feasibility": feasibility, "roi": roi_score, "time_to_value": ttv, "confidence": confidence}
    missing = [k for k, v in dims.items() if v < 0.01]
    scored = {k: v for k, v in dims.items() if v >= 0.01}

    # Re-normalize composite weights over available dimensions
    if scored:
        total_w = sum(weights[k] for k in scored)
        composite = sum((weights[k] / total_w) * v for k, v in scored.items()) if total_w > 0 else 0.0
    else:
        composite = 0.0

    return {
        "feasibility": round(dims["feasibility"], 3) if dims["feasibility"] >= 0.01 else None,
        "roi": round(dims["roi"], 3) if dims["roi"] >= 0.01 else None,
        "time_to_value": round(dims["time_to_value"], 3) if dims["time_to_value"] >= 0.01 else None,
        "confidence": round(dims["confidence"], 3) if dims["confidence"] >= 0.01 else None,
        "composite": round(composite, 4),
        "data_sufficiency": "scored" if not missing else "insufficient_data",
        "missing_dimensions": missing,
    }
