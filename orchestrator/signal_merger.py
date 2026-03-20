"""Signal merger — merges user-provided hints into scraped SignalSet."""
from __future__ import annotations

from orchestrator.schemas import UserHints

_USER_HINT_CONFIDENCE = 0.85


def _make_signal(sig_type: str, value: str) -> dict:
    return {
        "signal_id": "",
        "type": sig_type,
        "value": value,
        "source": "user_hint",
        "confidence": _USER_HINT_CONFIDENCE,
        "raw_quote": "",
    }


def _dedup(existing: list[dict], incoming: list[dict]) -> list[dict]:
    """Merge incoming signals, keeping higher-confidence on type+value collision."""
    index: dict[tuple[str, str], int] = {}
    merged = list(existing)
    for i, sig in enumerate(merged):
        key = (sig.get("type", ""), sig.get("value", "").lower())
        index[key] = i
    for sig in incoming:
        key = (sig.get("type", ""), sig.get("value", "").lower())
        if key in index:
            existing_conf = merged[index[key]].get("confidence", 0.0)
            if sig.get("confidence", 0.0) > existing_conf:
                merged[index[key]] = sig
        else:
            index[key] = len(merged)
            merged.append(sig)
    return merged


def merge_signals(scraped_signals: dict, user_hints: UserHints | None) -> dict:
    """Merge user hints into scraped signals dict.

    Returns the same dict shape as SignalSet.model_dump().
    If user_hints is None the scraped dict is returned unchanged.
    """
    if user_hints is None:
        return scraped_signals

    result = dict(scraped_signals)
    existing: list[dict] = list(result.get("signals", []))
    incoming: list[dict] = []

    for pain in user_hints.pain_points:
        incoming.append(_make_signal("pain_point", pain))

    for tech in user_hints.known_tech:
        incoming.append(_make_signal("tech_stack", tech))

    if user_hints.employee_count is not None:
        incoming.append(_make_signal("scale_hint", str(user_hints.employee_count)))

    if user_hints.context:
        incoming.append(_make_signal("intent_signal", user_hints.context))

    result["signals"] = _dedup(existing, incoming)

    if user_hints.industry and user_hints.industry != result.get("industry", ""):
        result["industry"] = user_hints.industry

    return result
