"""Tests for MaturityScorerAgent."""
from __future__ import annotations

from agents.maturity_scorer import MaturityScorerAgent


def test_dry_run_returns_maturity(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    agent = MaturityScorerAgent()
    result = agent.run({"signals": []})
    assert isinstance(result, dict), "Expected dict result in dry-run"
    assert "dimensions" in result
    assert "composite_score" in result
    assert "composite_label" in result
    dims = result["dimensions"]
    assert len(dims) == 4
    for dim_name, dim_data in dims.items():
        assert "score" in dim_data
        assert isinstance(dim_data["score"], (int, float))


def test_build_prompt_includes_signals():
    agent = MaturityScorerAgent()
    signals = [{"signal_id": "sig-001", "type": "tech_stack", "value": "BigQuery"}]
    prompt = agent._build_prompt(signals)
    assert "sig-001" in prompt
    assert "BigQuery" in prompt
    assert "Signals:" in prompt
