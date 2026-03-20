"""Question engine — deterministic confidence gap analyzer, no LLM call."""

from __future__ import annotations

_GENERIC_QUESTIONS = [
    {
        "question": "What is your biggest manual process or operational bottleneck?",
        "dimension": "pain_point_match",
        "current_score": 0.0,
        "potential_lift": 0.20,
        "why": "Identifying pain points anchors the use case to a real problem",
    },
    {
        "question": "What is your current tech stack for data and infrastructure?",
        "dimension": "tech_feasibility",
        "current_score": 0.0,
        "potential_lift": 0.18,
        "why": "Knowing the data layer determines which solutions are feasible",
    },
    {
        "question": "Can you share specific volume numbers — transactions, documents, headcount?",
        "dimension": "evidence_depth",
        "current_score": 0.0,
        "potential_lift": 0.15,
        "why": "Concrete numbers anchor ROI estimates and size the opportunity",
    },
]

_DIMENSION_QUESTIONS = {
    "pain_point_match": (
        "What is your biggest manual process or operational bottleneck?",
        0.15,
        "Confirming pain point strengthens the top match",
    ),
    "tech_feasibility": (
        "What is your current tech stack for data and infrastructure?",
        0.14,
        "Tech stack confirmation raises feasibility confidence",
    ),
    "scale_match": (
        "How large is the team affected by this problem?",
        0.12,
        "Headcount confirms whether scale matches the solution profile",
    ),
    "maturity_fit": (
        "Have you tried any AI or automation initiatives before?",
        0.12,
        "Prior AI experience affects implementation readiness",
    ),
    "evidence_depth": (
        "Can you share specific volume numbers — transactions, documents, headcount?",
        0.10,
        "Concrete numbers anchor ROI estimates and size the opportunity",
    ),
}

_SKIP_DIMENSIONS = {"industry_match"}


def generate_questions(match_results: dict, signals: dict) -> list[dict]:
    """Return top 3 questions ranked by potential confidence lift.

    Analyzes the top delivered match's confidence_breakdown.
    Falls back to generic discovery questions when no breakdown exists.

    Each returned dict has keys: question, dimension, current_score,
    potential_lift, why.
    """
    delivered = match_results.get("delivered", [])
    top_match = delivered[0] if delivered else None
    breakdown: dict | None = None

    if top_match and isinstance(top_match, dict):
        breakdown = top_match.get("confidence_breakdown")

    if not breakdown:
        return _GENERIC_QUESTIONS[:3]

    candidates: list[dict] = []
    for dim, (question, lift, why) in _DIMENSION_QUESTIONS.items():
        if dim in _SKIP_DIMENSIONS:
            continue
        score = breakdown.get(dim, 1.0)
        if isinstance(score, (int, float)) and score < 0.6:
            candidates.append(
                {
                    "question": question,
                    "dimension": dim,
                    "current_score": round(float(score), 3),
                    "potential_lift": lift,
                    "why": why,
                }
            )

    candidates.sort(key=lambda x: x["potential_lift"], reverse=True)
    return candidates[:3] if candidates else _GENERIC_QUESTIONS[:3]
