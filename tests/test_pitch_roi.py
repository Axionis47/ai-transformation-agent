"""Tests for engines/pitch/roi_model.py -- ROI translation and scaling logic."""
from __future__ import annotations

import pytest
from engines.pitch.roi_model import translate_roi, ROIEstimate

ENGAGEMENT_LOOKUP = {
    "eng-001": {
        "industry": "financial_services",
        "company_size_band": "200-500",
        "timeline_weeks": 8,
        "measured_impact": {"ticket_reduction_pct": 87, "agent_hours_saved": 210},
    },
}


def test_roi_same_band_same_industry():
    result = translate_roi(["eng-001"], "200-500", "financial_services", ENGAGEMENT_LOOKUP)
    assert result is not None
    assert isinstance(result, ROIEstimate)
    assert result.size_factor == 1.0
    assert result.industry_factor == 1.0
    assert result.adjusted_value == result.base_value


def test_roi_smaller_band_scales_down():
    result = translate_roi(["eng-001"], "100-200", "financial_services", ENGAGEMENT_LOOKUP)
    assert result is not None
    assert result.adjusted_value < result.base_value


def test_roi_different_industry_discounts():
    result = translate_roi(["eng-001"], "200-500", "manufacturing", ENGAGEMENT_LOOKUP)
    assert result is not None
    assert result.industry_factor < 1.0
    assert result.adjusted_value < result.base_value


def test_roi_no_engagement_returns_none():
    result = translate_roi([], "200-500", "financial_services", ENGAGEMENT_LOOKUP)
    assert result is None


def test_roi_sensitivity_output():
    result = translate_roi(["eng-001"], "200-500", "financial_services", ENGAGEMENT_LOOKUP)
    assert result is not None
    sensitivity = result.sensitivity
    assert "size_factor_high" in sensitivity
    assert "size_factor_low" in sensitivity
    assert "industry_factor_high" in sensitivity
    assert "industry_factor_low" in sensitivity
