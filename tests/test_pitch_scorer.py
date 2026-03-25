"""Tests for engines/pitch/scorer.py -- four-dimension opportunity scoring."""
from __future__ import annotations

from engines.pitch.matcher import TemplateMatch
from engines.pitch.roi_model import ROIEstimate
from engines.pitch.scorer import score_opportunity
from engines.pitch.templates import get_templates

_CONFIG = {
    "scoring": {"w_roi": 0.30, "w_feasibility": 0.30, "w_ttv": 0.20, "w_confidence": 0.20}
}


def _make_match(matched_engagement_ids=None, llm_scores=None, template_idx=0):
    template = get_templates()[template_idx]
    return TemplateMatch(
        template=template,
        match_score=0.6,
        matched_evidence_ids=["ev-001"],
        matched_engagement_ids=matched_engagement_ids or [],
        llm_scores=llm_scores or {},
    )


def _make_roi(adjusted_value=60.0, timeline_weeks=8):
    return ROIEstimate(
        primary_metric="ticket_reduction", base_value=60.0,
        adjusted_value=adjusted_value, size_factor=1.0, industry_factor=1.0,
        source_engagement_id="eng-001", timeline_weeks=timeline_weeks,
        assumptions={}, sensitivity={},
    )


def test_scorer_uses_llm_scores():
    llm = {"feasibility": 0.85, "roi": 0.9, "time_to_value": 0.7, "confidence": 0.8}
    match = _make_match(llm_scores=llm)
    scores = score_opportunity(match, _make_roi(), _CONFIG)
    assert scores["feasibility"] == 0.85
    assert scores["roi"] == 0.9


def test_scorer_fallback_when_no_llm():
    match = _make_match(matched_engagement_ids=["eng-001"])
    scores = score_opportunity(match, _make_roi(), _CONFIG)
    # Fallback: engagement exists -> feasibility 0.7
    assert scores["feasibility"] == 0.7


def test_scorer_composite_formula():
    llm = {"feasibility": 0.8, "roi": 0.7, "time_to_value": 0.6, "confidence": 0.5}
    match = _make_match(llm_scores=llm)
    scores = score_opportunity(match, _make_roi(), _CONFIG)
    expected = 0.30 * 0.7 + 0.30 * 0.8 + 0.20 * 0.6 + 0.20 * 0.5
    assert abs(scores["composite"] - round(expected, 4)) < 0.001


def test_scorer_all_scores_bounded():
    match = _make_match()
    scores = score_opportunity(match, _make_roi(), _CONFIG)
    for key in ("feasibility", "roi", "time_to_value", "confidence", "composite"):
        assert 0.0 <= scores[key] <= 1.0


def test_scorer_no_roi_low_score():
    match = _make_match()
    scores = score_opportunity(match, None, _CONFIG)
    assert scores["roi"] == 0.3
