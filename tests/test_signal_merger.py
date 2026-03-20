"""Tests for signal merger and ConfidenceBreakdown schema."""
from __future__ import annotations

from orchestrator.schemas import ConfidenceBreakdown, MatchResult, UserHints
from orchestrator.signal_merger import merge_signals


def _make_scraped(signals: list[dict] | None = None) -> dict:
    return {
        "signals": signals or [],
        "industry": "retail",
        "scale": "mid-market",
        "confidence_level": "MEDIUM",
        "signal_count": len(signals or []),
    }


def test_merge_none_hints_returns_unchanged():
    scraped = _make_scraped()
    assert merge_signals(scraped, None) is scraped


def test_merge_adds_pain_point_with_user_hint_source():
    hints = UserHints(pain_points=["we cannot predict demand accurately"])
    result = merge_signals(_make_scraped(), hints)
    pp = [s for s in result["signals"] if s["type"] == "pain_point"]
    assert len(pp) == 1
    assert pp[0]["source"] == "user_hint"
    assert pp[0]["confidence"] == 0.85


def test_merge_adds_tech_stack_signals():
    hints = UserHints(known_tech=["Snowflake", "dbt"])
    result = merge_signals(_make_scraped(), hints)
    values = {s["value"] for s in result["signals"] if s["type"] == "tech_stack"}
    assert {"Snowflake", "dbt"} <= values


def test_merge_overrides_industry_from_hints():
    hints = UserHints(industry="logistics")
    result = merge_signals(_make_scraped(), hints)
    assert result["industry"] == "logistics"



def test_merge_dedup_keeps_higher_confidence():
    scraped = _make_scraped([
        {"type": "tech_stack", "value": "python", "source": "about_text",
         "confidence": 0.5, "signal_id": "s1", "raw_quote": ""},
    ])
    hints = UserHints(known_tech=["Python"])
    result = merge_signals(scraped, hints)
    python_sigs = [s for s in result["signals"]
                   if s["type"] == "tech_stack" and s["value"].lower() == "python"]
    assert len(python_sigs) == 1
    assert python_sigs[0]["source"] == "user_hint"



def test_confidence_breakdown_defaults():
    cb = ConfidenceBreakdown()
    assert cb.evidence_ceiling == "url_only"
    assert cb.overall == 0.0


def test_confidence_breakdown_in_match_result():
    cb = ConfidenceBreakdown(
        industry_match=1.0, evidence_ceiling="url_plus_hints", overall=0.88
    )
    mr = MatchResult(match_tier="DELIVERED", confidence_breakdown=cb)
    assert mr.confidence_breakdown.evidence_ceiling == "url_plus_hints"
    assert mr.confidence_breakdown.overall == 0.88
