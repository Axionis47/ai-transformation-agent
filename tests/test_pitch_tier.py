"""Tests for engines/pitch/tier_classifier.py -- EASY/MEDIUM/HARD classification."""

from __future__ import annotations

from core.schemas import OpportunityTier
from engines.pitch.matcher import TemplateMatch
from engines.pitch.templates import get_templates
from engines.pitch.tier_classifier import classify_tier


def _make_match(
    match_score: float,
    matched_engagement_ids: list[str],
    tier_override: str | None = None,
    adaptation_needed: str | None = None,
) -> TemplateMatch:
    template = get_templates()[0]  # tpl-support-auto
    return TemplateMatch(
        template=template,
        match_score=match_score,
        matched_evidence_ids=["ev-001"],
        matched_engagement_ids=matched_engagement_ids,
        tier_override=tier_override,
        adaptation_needed=adaptation_needed,
    )


LOOKUP = {"eng-001": {"industry": "financial_services", "company_size_band": "200-500"}}


def test_llm_tier_override_easy():
    match = _make_match(0.7, ["eng-001"], tier_override="EASY")
    tier, adaptation = classify_tier(match, "financial_services", LOOKUP)
    assert tier == OpportunityTier.EASY
    assert adaptation is None


def test_llm_tier_override_medium_with_adaptation():
    match = _make_match(0.5, ["eng-001"], tier_override="MEDIUM", adaptation_needed="Needs industry adaptation")
    tier, adaptation = classify_tier(match, "financial_services", LOOKUP)
    assert tier == OpportunityTier.MEDIUM
    assert adaptation == "Needs industry adaptation"


def test_llm_tier_override_hard():
    match = _make_match(0.2, [], tier_override="HARD")
    tier, _ = classify_tier(match, "financial_services", LOOKUP)
    assert tier == OpportunityTier.HARD


def test_fallback_high_score_easy():
    match = _make_match(0.7, ["eng-001"])
    tier, _ = classify_tier(match, "financial_services", LOOKUP)
    assert tier == OpportunityTier.EASY


def test_fallback_no_engagement_hard():
    match = _make_match(0.9, [])
    tier, _ = classify_tier(match, "financial_services", LOOKUP)
    assert tier == OpportunityTier.HARD


def test_fallback_medium_score():
    match = _make_match(0.4, ["eng-001"])
    tier, _ = classify_tier(match, "financial_services", LOOKUP)
    assert tier == OpportunityTier.MEDIUM
