from __future__ import annotations

from core.schemas import OpportunityTier
from engines.pitch.matcher import TemplateMatch


def classify_tier(
    match: TemplateMatch,
    company_industry: str,
    engagement_lookup: dict[str, dict],
) -> tuple[OpportunityTier, str | None]:
    """Classify an opportunity into EASY, MEDIUM, or HARD.

    Returns (tier, adaptation_needed_text).
    adaptation_needed_text is None for EASY and HARD tiers.
    """
    if not match.matched_engagement_ids:
        return OpportunityTier.HARD, None

    # Check if any matched engagement is in same industry
    same_industry_eng_ids = [
        eng_id for eng_id in match.matched_engagement_ids
        if eng_id in engagement_lookup
        and engagement_lookup[eng_id].get("industry", "") == company_industry
    ]

    # Check size band differences
    different_size_eng_ids = [
        eng_id for eng_id in match.matched_engagement_ids
        if eng_id in engagement_lookup
        and engagement_lookup[eng_id].get("company_size_band") is not None
    ]

    if same_industry_eng_ids and match.match_score >= 0.4:
        return OpportunityTier.EASY, None

    if same_industry_eng_ids and match.match_score >= 0.2:
        return OpportunityTier.MEDIUM, (
            f"Match score {match.match_score:.2f} is below high-confidence threshold; "
            "additional validation recommended before committing."
        )

    # Different industry: find one example to explain the gap
    diff_eng_ids = [
        eng_id for eng_id in match.matched_engagement_ids
        if eng_id in engagement_lookup
        and engagement_lookup[eng_id].get("industry", "") != company_industry
    ]
    if diff_eng_ids:
        eng = engagement_lookup[diff_eng_ids[0]]
        eng_industry = eng.get("industry", "unknown")
        adaptation = (
            f"Closest evidence is from {eng_industry}, not {company_industry}. "
            "Industry-specific data pipelines and regulatory context will need adaptation."
        )
        return OpportunityTier.MEDIUM, adaptation

    return OpportunityTier.HARD, None
