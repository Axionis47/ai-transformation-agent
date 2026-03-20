"""Readiness score — deterministic pitch readiness calculator, no LLM call."""

from __future__ import annotations

_WEIGHTS = {
    "signal_completeness": 0.20,
    "match_confidence": 0.30,
    "pain_confirmation": 0.25,
    "roi_specificity": 0.25,
}

_LABELS = [
    (0.90, "High confidence"),
    (0.75, "Ready to pitch"),
    (0.50, "Foundation set — add context to sharpen"),
    (0.00, "Research phase"),
]

_NEXT_ACTIONS = {
    "signal_completeness": "Gather more context about their operations to raise signal coverage",
    "match_confidence": "Confirm their pain points and tech stack to sharpen match confidence",
    "pain_confirmation": "Ask directly about their biggest operational bottleneck to confirm pain",
    "roi_specificity": "Get their cost or volume baseline to anchor the ROI conversation",
}


def _label(score: float) -> str:
    for threshold, text in _LABELS:
        if score >= threshold:
            return text
    return "Research phase"


def _signal_completeness(signals: dict) -> float:
    count = len(signals.get("signals", []))
    return min(1.0, count / 10.0)


def _match_confidence(match_results: dict) -> float:
    delivered = match_results.get("delivered", [])
    if not delivered:
        return 0.3
    top = delivered[0]
    if isinstance(top, dict):
        return float(top.get("confidence", 0.3))
    return 0.3


def _pain_confirmation(signals: dict) -> float:
    raw_signals = signals.get("signals", [])
    pain_signals = [s for s in raw_signals if s.get("type") == "pain_point"]
    if not pain_signals:
        return 0.2
    has_hint = any(s.get("source") == "user_hint" for s in pain_signals)
    return 1.0 if has_hint else 0.5


def _roi_specificity(match_results: dict) -> float:
    delivered = match_results.get("delivered", [])
    if not delivered:
        return 0.2
    top = delivered[0]
    if not isinstance(top, dict):
        return 0.5
    metrics = top.get("proven_metrics")
    if metrics and isinstance(metrics, dict) and metrics.get("primary_value"):
        return 1.0
    return 0.5


def compute_readiness(signals: dict, match_results: dict, has_hints: bool) -> dict:
    """Return pitch readiness assessment as a structured dict."""
    components = {
        "signal_completeness": round(_signal_completeness(signals), 3),
        "match_confidence": round(_match_confidence(match_results), 3),
        "pain_confirmation": round(_pain_confirmation(signals), 3),
        "roi_specificity": round(_roi_specificity(match_results), 3),
    }

    score = round(
        sum(components[k] * _WEIGHTS[k] for k in _WEIGHTS),
        3,
    )

    weakest = min(components, key=lambda k: components[k])
    next_action = _NEXT_ACTIONS[weakest]

    return {
        "score": score,
        "label": _label(score),
        "components": components,
        "next_action": next_action,
    }
