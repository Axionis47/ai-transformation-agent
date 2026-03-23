"""Tests for engines/pitch/scorer.py -- four-dimension opportunity scoring."""
from __future__ import annotations

import pytest
from core.schemas import EvidenceItem, EvidenceSource
from engines.pitch.matcher import TemplateMatch
from engines.pitch.roi_model import ROIEstimate
from engines.pitch.scorer import score_opportunity
from engines.pitch.templates import get_templates

_CONFIG = {
    "scoring": {"w_roi": 0.30, "w_feasibility": 0.30, "w_ttv": 0.20, "w_confidence": 0.20}
}


def _make_match(anti_signal_hits=None, matched_engagement_ids=None, template_idx=0):
    template = get_templates()[template_idx]
    return TemplateMatch(
        template=template,
        match_score=0.6,
        win_signal_hits=["support"],
        anti_signal_hits=anti_signal_hits or [],
        matched_evidence_ids=["ev-001"],
        matched_engagement_ids=matched_engagement_ids or [],
    )


def _make_roi(adjusted_value=60.0, timeline_weeks=8):
    return ROIEstimate(
        primary_metric="ticket_reduction",
        base_value=60.0,
        adjusted_value=adjusted_value,
        size_factor=1.0,
        industry_factor=1.0,
        source_engagement_id="eng-001",
        timeline_weeks=timeline_weeks,
        assumptions={},
        sensitivity={},
    )


def test_scorer_uses_config_weights():
    match = _make_match()
    scores = score_opportunity(match, _make_roi(), _CONFIG)
    expected_composite = (
        0.30 * scores["roi"]
        + 0.30 * scores["feasibility"]
        + 0.20 * scores["time_to_value"]
        + 0.20 * scores["confidence"]
    )
    assert abs(scores["composite"] - round(expected_composite, 4)) < 0.001


def test_scorer_no_anti_signals_high_feasibility():
    match = _make_match(anti_signal_hits=[])
    scores = score_opportunity(match, _make_roi(), _CONFIG)
    assert scores["feasibility"] >= 0.9


def test_scorer_short_timeline_high_ttv():
    match = _make_match()
    roi = _make_roi(timeline_weeks=8)
    scores = score_opportunity(match, roi, _CONFIG)
    assert scores["time_to_value"] >= 0.9


def test_scorer_composite_formula():
    match = _make_match()
    scores = score_opportunity(match, _make_roi(), _CONFIG)
    assert 0.0 <= scores["composite"] <= 1.0
    for key in ("feasibility", "roi", "time_to_value", "confidence"):
        assert 0.0 <= scores[key] <= 1.0


def test_scorer_no_roi_low_score():
    match = _make_match()
    scores = score_opportunity(match, None, _CONFIG)
    assert scores["roi"] == 0.3
