"""Tests for deterministic VictoryMatcher."""
from __future__ import annotations

import pytest
from orchestrator.victory_matcher import match_victories


def _make_win(win_id: str, industry: str, size: str, maturity: str) -> dict:
    return {
        "id": win_id,
        "engagement_title": f"Test engagement {win_id}",
        "industry": industry,
        "company_profile": {"size_label": size},
        "maturity_at_engagement": maturity,
        "results": {"primary_metric": {"label": "Cost Reduction", "value": "10%"}},
    }


def test_direct_match_same_industry():
    wins = [_make_win("w1", "logistics", "mid-market", "Developing")]
    results = match_victories("logistics", "mid-market", "Developing", wins)
    assert results[0].match_tier == "DIRECT_MATCH"
    assert results[0].similarity_score == pytest.approx(1.0)


def test_calibration_match_related_industry():
    # Related industry (0.2) + mismatched maturity (0.0) + mismatched size (0.0) = 0.2 → ADJACENT
    # Related industry (0.2) + adjacent maturity (0.2) + same size (0.2) = 0.6 → CALIBRATION
    wins = [_make_win("w1", "manufacturing", "mid-market", "Emerging")]
    results = match_victories("logistics", "mid-market", "Developing", wins)
    assert results[0].match_tier == "CALIBRATION_MATCH"


def test_adjacent_match_unrelated():
    wins = [_make_win("w1", "healthcare", "enterprise", "Advanced")]
    results = match_victories("logistics", "mid-market", "Developing", wins)
    assert results[0].match_tier == "ADJACENT_MATCH"


def test_sorting_direct_before_calibration():
    wins = [
        _make_win("w1", "healthcare", "enterprise", "Advanced"),
        _make_win("w2", "logistics", "mid-market", "Developing"),
    ]
    results = match_victories("logistics", "mid-market", "Developing", wins)
    assert results[0].match_tier == "DIRECT_MATCH"
    assert results[1].match_tier == "ADJACENT_MATCH"


def test_confidence_floors():
    direct_win = [_make_win("w1", "logistics", "mid-market", "Developing")]
    adjacent_win = [_make_win("w2", "healthcare", "enterprise", "Advanced")]

    direct_results = match_victories("logistics", "mid-market", "Developing", direct_win)
    adjacent_results = match_victories("logistics", "startup", "Beginner", adjacent_win)

    assert direct_results[0].confidence >= 0.75
    assert adjacent_results[0].confidence >= 0.40


def _make_win_calibrated(win_id: str, maturity: str) -> dict:
    """Build a victory record that includes calibration fields."""
    win = _make_win(win_id, "logistics", "mid-market", maturity)
    win["industry_benchmark"] = "14% fuel cost reduction on $2.1M fleet spend"
    win["success_threshold"] = "Applicable when TMS is in place."
    win["gap_analysis_template"] = "Maturity gap of {gap} points from engagement baseline."
    return win


def test_gap_analysis_populated_when_calibration_fields_present():
    """Victory with calibration fields produces non-null gap_analysis."""
    wins = [_make_win_calibrated("w1", "Developing")]
    # company score 1.3, victory maturity "Developing"=2.0 → gap = 0.7
    results = match_victories("logistics", "mid-market", "Beginner", wins,
                              company_composite_score=1.3)
    assert results[0].gap_analysis is not None
    assert "0.7" in results[0].gap_analysis
    assert "14% fuel cost reduction" in results[0].gap_analysis


def test_gap_analysis_none_when_calibration_fields_absent():
    """Victory WITHOUT calibration fields yields gap_analysis=None, no exception."""
    wins = [_make_win("w1", "logistics", "mid-market", "Developing")]
    results = match_victories("logistics", "mid-market", "Developing", wins,
                              company_composite_score=2.0)
    assert results[0].gap_analysis is None


def test_gap_calculation_correct():
    """Gap = abs(company_score - victory_maturity_float), e.g. 1.3 vs Developing(2.0) = 0.7."""
    wins = [_make_win_calibrated("w1", "Developing")]
    results = match_victories("logistics", "mid-market", "Beginner", wins,
                              company_composite_score=1.3)
    gap_text = results[0].gap_analysis or ""
    assert "0.7" in gap_text
