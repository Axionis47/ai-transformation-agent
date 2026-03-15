"""Tests for agents/consultant.py — format_wins, dry-run, prompt loading."""

from __future__ import annotations

from agents.consultant import ConsultantAgent, format_wins


# ---------------------------------------------------------------------------
# format_wins — full victory record (nested dicts)
# ---------------------------------------------------------------------------

_FULL_WIN = {
    "id": "win-001",
    "engagement_title": "Route Optimization for Regional LTL Carrier",
    "industry": "logistics",
    "company_profile": {"size_label": "mid-market"},
    "maturity_at_engagement": "Developing",
    "problem_statement": "Manual dispatch causing 18% fuel cost increase.",
    "solution_summary": "ML route engine integrated into existing TMS.",
    "results": {
        "primary_metric": {
            "label": "Fuel Cost Reduction",
            "value": "14%",
            "baseline": "$2.1M annual",
            "outcome": "$1.8M annual",
        },
        "measurement_period": "6 months post-launch",
    },
    "engagement_details": {"duration_months": 4, "tenex_team_size": 3},
}


def test_format_wins_full_record_contains_win_id():
    result = format_wins([_FULL_WIN])
    assert "win-001" in result


def test_format_wins_full_record_contains_title():
    result = format_wins([_FULL_WIN])
    assert "Route Optimization for Regional LTL Carrier" in result


def test_format_wins_full_record_contains_metric():
    result = format_wins([_FULL_WIN])
    assert "Fuel Cost Reduction" in result
    assert "14%" in result


def test_format_wins_full_record_contains_baseline_outcome():
    result = format_wins([_FULL_WIN])
    assert "$2.1M annual" in result
    assert "$1.8M annual" in result


# ---------------------------------------------------------------------------
# format_wins — flat ChromaDB result shape
# ---------------------------------------------------------------------------

_FLAT_WIN = {
    "id": "win-002",
    "engagement_title": "Demand Forecasting for Mid-Market Retailer",
    "industry": "retail",
    "size_label": "mid-market",
    "maturity_at_engagement": "Emerging",
    "problem_statement": "Seasonal overstaffing and stockouts.",
    "solution_summary": "Demand forecasting from 3 years order history.",
    "primary_metric_label": "Warehouse Cost Reduction",
    "primary_metric_value": "25%",
    "measurement_period": "Q4 2024",
    "duration_months": 3,
}


def test_format_wins_flat_record_contains_win_id():
    result = format_wins([_FLAT_WIN])
    assert "win-002" in result


def test_format_wins_flat_record_size_from_flat_field():
    result = format_wins([_FLAT_WIN])
    assert "mid-market" in result


def test_format_wins_flat_record_metric():
    result = format_wins([_FLAT_WIN])
    assert "Warehouse Cost Reduction" in result
    assert "25%" in result


# ---------------------------------------------------------------------------
# format_wins — edge cases
# ---------------------------------------------------------------------------

def test_format_wins_empty_list():
    result = format_wins([])
    assert "No relevant Tenex delivery wins found." in result


def test_format_wins_multiple_wins_separated():
    result = format_wins([_FULL_WIN, _FLAT_WIN])
    assert "win-001" in result
    assert "win-002" in result
    # Wins are separated by double newline
    assert "\n\n" in result


def test_format_wins_truncates_long_problem():
    long_win = dict(_FULL_WIN)
    long_win["problem_statement"] = "x" * 500
    result = format_wins([long_win])
    # problem is capped at 200 chars
    assert "x" * 201 not in result


# ---------------------------------------------------------------------------
# ConsultantAgent — dry-run
# ---------------------------------------------------------------------------

def test_consultant_dry_run_returns_dict(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    agent = ConsultantAgent()
    result = agent._run({})
    assert isinstance(result, dict)


def test_consultant_dry_run_has_maturity_score(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    agent = ConsultantAgent()
    result = agent._run({})
    assert "maturity_score" in result


def test_load_prompt_uses_wins_label():
    agent = ConsultantAgent()
    prompt = agent._load_prompt({"name": "ACME"}, [_FULL_WIN])
    assert "Relevant Tenex delivery wins" in prompt
    assert "win-001" in prompt
