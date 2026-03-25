"""Tier classification — uses LLM evaluation from matcher.

No if/else rules. The LLM decides the tier during opportunity evaluation.
This module reads the LLM's decision and applies it.
"""
from __future__ import annotations

from core.schemas import OpportunityTier
from engines.pitch.matcher import TemplateMatch


def classify_tier(
    match: TemplateMatch,
    company_industry: str,
    engagement_lookup: dict[str, dict],
) -> tuple[OpportunityTier, str | None]:
    """Classify tier using the LLM's evaluation from the matching step.

    Returns (tier, adaptation_needed_text).
    """
    # Use LLM's tier decision if available
    if match.tier_override:
        tier_str = match.tier_override.upper()
        tier_map = {"EASY": OpportunityTier.EASY, "MEDIUM": OpportunityTier.MEDIUM, "HARD": OpportunityTier.HARD}
        tier = tier_map.get(tier_str, OpportunityTier.MEDIUM)
        adaptation = match.adaptation_needed if tier == OpportunityTier.MEDIUM else None
        return tier, adaptation

    # Fallback: classify based on engagement match and score
    if not match.matched_engagement_ids:
        return OpportunityTier.HARD, None

    if match.match_score >= 0.6:
        return OpportunityTier.EASY, None
    if match.match_score >= 0.3:
        return OpportunityTier.MEDIUM, match.adaptation_needed or "Further validation recommended."

    return OpportunityTier.HARD, None
