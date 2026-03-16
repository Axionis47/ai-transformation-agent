"""Victory matcher — deterministic relevance scoring for RAG results."""
from __future__ import annotations

from orchestrator.schemas import VictoryMatch


def match_victories(
    signals_industry: str,
    signals_scale: str,
    maturity_label: str,
    rag_results: list[dict],
) -> list[VictoryMatch]:
    """Score and tier-classify RAG results against company signals.

    Deterministic scoring — no model call needed.

    Scoring:
    - industry_score (0-0.4): exact match=0.4, related=0.2, unrelated=0.0
    - maturity_score (0-0.4): same label=0.4, adjacent=0.2, distant=0.0
    - size_score (0-0.2): same size_label=0.2, adjacent=0.1, different=0.0

    Tier thresholds:
    - DIRECT_MATCH: total >= 0.7 AND industry match > 0
    - CALIBRATION_MATCH: total >= 0.4
    - ADJACENT_MATCH: below 0.4
    """
    MATURITY_LEVELS = ["Beginner", "Developing", "Emerging", "Advanced", "Leading"]
    SIZE_LEVELS = ["startup", "mid-market", "enterprise"]

    matches = []
    for win in rag_results:
        win_industry = win.get("industry", "")
        win_size = win.get("size_label", "")
        if not win_size:
            profile = win.get("company_profile", {})
            if isinstance(profile, dict):
                win_size = profile.get("size_label", "")
        win_maturity = win.get("maturity_at_engagement", "")

        if signals_industry.lower() == win_industry.lower():
            industry_score = 0.4
        elif _industries_related(signals_industry, win_industry):
            industry_score = 0.2
        else:
            industry_score = 0.0

        maturity_score = _proximity_score(maturity_label, win_maturity, MATURITY_LEVELS, 0.4)
        size_score = _proximity_score(signals_scale, win_size, SIZE_LEVELS, 0.2)

        total = industry_score + maturity_score + size_score

        if total >= 0.7 and industry_score > 0:
            tier = "DIRECT_MATCH"
            confidence = min(0.75 + (total - 0.7) * 0.5, 0.95)
        elif total >= 0.4:
            tier = "CALIBRATION_MATCH"
            confidence = min(0.55 + (total - 0.4) * 0.3, 0.95)
        else:
            tier = "ADJACENT_MATCH"
            confidence = min(0.40 + total * 0.3, 0.95)

        results = win.get("results", {})
        if isinstance(results, dict):
            pm = results.get("primary_metric", {})
            roi = f"{pm.get('label', '')}: {pm.get('value', '')}"
        else:
            roi = f"{win.get('primary_metric_label', '')}: {win.get('primary_metric_value', '')}"

        matches.append(VictoryMatch(
            win_id=win.get("id", "unknown"),
            engagement_title=win.get("engagement_title", "Untitled"),
            match_tier=tier,
            relevance_note=f"Industry: {win_industry}, Size: {win_size}, Maturity: {win_maturity}",
            roi_benchmark=roi.strip(": "),
            industry=win_industry,
            similarity_score=total,
            confidence=round(confidence, 2),
        ))

    tier_order = {"DIRECT_MATCH": 0, "CALIBRATION_MATCH": 1, "ADJACENT_MATCH": 2}
    matches.sort(key=lambda m: (tier_order.get(m.match_tier, 3), -m.similarity_score))
    return matches


def _proximity_score(value: str, target: str, levels: list[str], max_score: float) -> float:
    """Score based on proximity in an ordered list."""
    vi = levels.index(value) if value in levels else -1
    ti = levels.index(target) if target in levels else -1
    if vi < 0 or ti < 0:
        return 0.0
    distance = abs(vi - ti)
    if distance == 0:
        return max_score
    if distance == 1:
        return max_score * 0.5
    return 0.0


def _industries_related(a: str, b: str) -> bool:
    """Check if two industries are in the same cluster."""
    clusters = [
        {"logistics", "manufacturing", "construction", "energy"},
        {"financial_services", "fintech", "insurance"},
        {"healthcare", "healthtech"},
        {"retail", "ecommerce"},
        {"professional_services", "real_estate", "proptech"},
    ]
    a_lower, b_lower = a.lower(), b.lower()
    for cluster in clusters:
        if any(a_lower in c for c in cluster) and any(b_lower in c for c in cluster):
            return True
    return False
