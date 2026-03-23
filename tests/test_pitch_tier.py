"""Tests for engines/pitch/tier_classifier.py -- EASY/MEDIUM/HARD classification."""
from __future__ import annotations

import pytest
from core.schemas import OpportunityTier
from engines.pitch.matcher import TemplateMatch
from engines.pitch.templates import get_templates
from engines.pitch.tier_classifier import classify_tier


def _make_match(
    match_score: float,
    matched_engagement_ids: list[str],
) -> TemplateMatch:
    template = get_templates()[0]  # tpl-support-auto
    return TemplateMatch(
        template=template,
        match_score=match_score,
        win_signal_hits=["support"],
        anti_signal_hits=[],
        matched_evidence_ids=["ev-001"],
        matched_engagement_ids=matched_engagement_ids,
    )


SAME_INDUSTRY_LOOKUP = {
    "eng-001": {"industry": "financial_services", "company_size_band": "200-500"},
}

DIFF_INDUSTRY_LOOKUP = {
    "eng-001": {"industry": "logistics", "company_size_band": "200-500"},
}


def test_tier_easy_same_industry():
    match = _make_match(0.5, ["eng-001"])
    tier, adaptation = classify_tier(match, "financial_services", SAME_INDUSTRY_LOOKUP)
    assert tier == OpportunityTier.EASY
    assert adaptation is None


def test_tier_medium_different_industry():
    match = _make_match(0.5, ["eng-001"])
    tier, adaptation = classify_tier(match, "financial_services", DIFF_INDUSTRY_LOOKUP)
    assert tier == OpportunityTier.MEDIUM
    assert adaptation is not None
    assert "logistics" in adaptation


def test_tier_hard_no_engagement():
    match = _make_match(0.6, [])
    tier, adaptation = classify_tier(match, "financial_services", SAME_INDUSTRY_LOOKUP)
    assert tier == OpportunityTier.HARD
    assert adaptation is None


def test_tier_medium_low_score():
    match = _make_match(0.25, ["eng-001"])
    tier, adaptation = classify_tier(match, "financial_services", SAME_INDUSTRY_LOOKUP)
    assert tier == OpportunityTier.MEDIUM
    assert adaptation is not None


def test_tier_requires_engagement_for_easy():
    match = _make_match(0.9, [])
    tier, _ = classify_tier(match, "financial_services", SAME_INDUSTRY_LOOKUP)
    assert tier != OpportunityTier.EASY
