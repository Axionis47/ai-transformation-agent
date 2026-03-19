"""Unit tests for orchestrator/matching_layer.py — three-tier matching logic."""
from __future__ import annotations

import pytest
from orchestrator.matching_layer import match


def _make_delivered_record(win_id: str, industry: str, size: str, maturity: str,
                            applicable_signals: list[str] | None = None) -> dict:
    return {
        "id": win_id,
        "engagement_title": f"Test Engagement {win_id}",
        "industry": industry,
        "sector_tags": [],
        "company_profile": {"size_label": size, "size_employees": 100, "geography": "US"},
        "maturity_at_engagement": maturity,
        "results": {
            "primary_metric": {"label": "Cost Reduction", "value": "10%"},
            "measurement_period": "3 months",
        },
        "applicable_signals": applicable_signals or [],
        "tech_stack": {"ml_approach": "XGBoost regression"},
        "engagement_details": {"duration_months": 3},
    }


def _make_industry_record(case_id: str, industry: str, company_type: str,
                           applicable_signals: list[str] | None = None) -> dict:
    return {
        "id": case_id,
        "case_title": f"Industry Case {case_id}",
        "industry": industry,
        "sector_tags": [],
        "company_profile": {"company_name": "TestCo", "company_type": company_type},
        "ai_application": {"deployment_scale": "500 sites"},
        "reported_outcomes": {
            "headline_metric": "15% reduction",
            "source": "Test source 2024",
        },
        "applicable_signals": applicable_signals or ["ops_signal", "data_signal"],
    }


def _signals(industry: str, scale: str, signal_types: list[str] | None = None) -> dict:
    sigs = [{"type": t, "value": "v", "source": "about_text", "confidence": 0.9}
            for t in (signal_types or [])]
    return {"industry": industry, "scale": scale, "signals": sigs}


def _maturity(label: str, score: float) -> dict:
    return {"composite_label": label, "composite_score": score}


# --- DELIVERED track tests ---

def test_delivered_confidence_band():
    """All DELIVERED matches must have confidence >= 0.80."""
    wins = [_make_delivered_record("w1", "logistics", "mid-market", "Developing")]
    result = match(_signals("logistics", "mid-market"), _maturity("Developing", 2.0), wins, [])
    assert len(result["delivered"]) > 0
    for mr in result["delivered"]:
        assert mr.confidence >= 0.80
        assert mr.match_tier == "DELIVERED"


def test_delivered_confidence_max():
    """DELIVERED confidence must not exceed 0.95."""
    wins = [_make_delivered_record("w1", "logistics", "mid-market", "Developing")]
    result = match(_signals("logistics", "mid-market"), _maturity("Developing", 2.0), wins, [])
    for mr in result["delivered"]:
        assert mr.confidence <= 0.95


def test_delivered_source_library():
    """DELIVERED results must have source_library = tenex_delivered."""
    wins = [_make_delivered_record("w1", "logistics", "mid-market", "Developing")]
    result = match(_signals("logistics", "mid-market"), _maturity("Developing", 2.0), wins, [])
    for mr in result["delivered"]:
        assert mr.source_library == "tenex_delivered"


# --- ADAPTATION track tests ---

def test_adaptation_confidence_band():
    """ADAPTATION matches must have confidence in 0.55-0.79."""
    # related industry (0.2) + missing maturity → neutral 0.15 + mismatched size (0.0) = 0.35
    # 0.35 >= 0.30 → ADAPTATION
    record = _make_delivered_record("w1", "manufacturing", "startup", "Emerging")
    record["maturity_at_engagement"] = ""  # missing maturity field
    wins = [record]
    result = match(_signals("logistics", "enterprise"), _maturity("Developing", 2.0), wins, [])
    # manufacturing ~ logistics (related), missing maturity → 0.15, size mismatch → 0.35 ADAPTATION
    assert len(result["adaptation"]) > 0
    for mr in result["adaptation"]:
        assert 0.55 <= mr.confidence <= 0.79
        assert mr.match_tier == "ADAPTATION"


def test_adaptation_has_base_solution_id():
    """ADAPTATION results must reference the base solution ID."""
    record = _make_delivered_record("w-adapt", "manufacturing", "startup", "Emerging")
    record["maturity_at_engagement"] = ""
    wins = [record]
    result = match(_signals("logistics", "enterprise"), _maturity("Developing", 2.0), wins, [])
    for mr in result["adaptation"]:
        assert mr.base_solution_id == "w-adapt"


# --- AMBITIOUS track tests ---

def test_ambitious_confidence_band():
    """AMBITIOUS matches must have confidence in 0.40-0.65."""
    cases = [_make_industry_record("ind-1", "logistics", "mid-market",
                                   ["ops_signal", "data_signal"])]
    result = match(
        _signals("logistics", "mid-market", ["ops_signal"]),
        _maturity("Developing", 2.0),
        [],
        cases,
    )
    assert len(result["ambitious"]) > 0
    for mr in result["ambitious"]:
        assert 0.40 <= mr.confidence <= 0.65
        assert mr.match_tier == "AMBITIOUS"


def test_ambitious_source_library():
    """AMBITIOUS results must have source_library = industry_cases."""
    cases = [_make_industry_record("ind-1", "logistics", "mid-market")]
    result = match(_signals("logistics", "mid-market", ["ops_signal"]), _maturity("Developing", 2.0),
                   [], cases)
    for mr in result["ambitious"]:
        assert mr.source_library == "industry_cases"


# --- Mutual exclusion ---

def test_record_cannot_appear_in_both_delivered_and_adaptation():
    """A Library A record may appear in DELIVERED or ADAPTATION, not both."""
    low_record = _make_delivered_record("w2", "manufacturing", "startup", "Emerging")
    low_record["maturity_at_engagement"] = ""  # missing maturity → 0.35 score → ADAPTATION
    wins = [
        _make_delivered_record("w1", "logistics", "mid-market", "Developing"),  # 1.0 → DELIVERED
        low_record,
    ]
    result = match(_signals("logistics", "enterprise"), _maturity("Developing", 2.0), wins, [])
    delivered_ids = {mr.source_id for mr in result["delivered"]}
    adaptation_ids = {mr.source_id for mr in result["adaptation"]}
    assert delivered_ids.isdisjoint(adaptation_ids), "Records appear in both DELIVERED and ADAPTATION"


# --- Empty input ---

def test_empty_inputs_return_all_three_keys():
    """Empty delivered and industry results return dict with all three keys, all empty."""
    result = match({}, {}, [], [])
    assert set(result.keys()) == {"delivered", "adaptation", "ambitious"}
    assert result["delivered"] == []
    assert result["adaptation"] == []
    assert result["ambitious"] == []


def test_partial_empty_inputs():
    """No industry results means ambitious is empty; delivered results still scored."""
    wins = [_make_delivered_record("w1", "logistics", "mid-market", "Developing")]
    result = match(_signals("logistics", "mid-market"), _maturity("Developing", 2.0), wins, [])
    assert result["ambitious"] == []
    assert len(result["delivered"]) + len(result["adaptation"]) > 0
