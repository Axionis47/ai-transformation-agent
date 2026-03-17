"""Unit tests for SignalExtractorAgent."""
from __future__ import annotations



def test_dry_run_returns_signals(monkeypatch):
    """Dry-run returns fixture signals with signal_ids present."""
    monkeypatch.setenv("DRY_RUN", "true")
    from agents.signal_extractor import SignalExtractorAgent

    agent = SignalExtractorAgent()
    result = agent.run({"company_data": {}})

    assert isinstance(result, dict), "Expected dict from dry-run"
    assert "signals" in result, "Expected 'signals' key in result"
    assert len(result["signals"]) > 0, "Expected at least one signal"
    signal_ids = [s.get("signal_id") for s in result["signals"]]
    assert all(sid is not None for sid in signal_ids), "All signals must have signal_id"


def test_build_prompt_includes_sections(monkeypatch):
    """_build_prompt includes about, careers, and product sections."""
    monkeypatch.setenv("DRY_RUN", "false")
    from agents.signal_extractor import SignalExtractorAgent

    agent = SignalExtractorAgent()
    company_data = {
        "url": "https://example.com",
        "about_text": "We are a SaaS company.",
        "job_postings": ["Senior Engineer — Python, Kubernetes"],
        "product_text": "Our platform helps logistics teams.",
    }
    prompt = agent._build_prompt(company_data)

    assert "ABOUT PAGE" in prompt
    assert "JOB POSTINGS" in prompt
    assert "PRODUCT/SOLUTIONS PAGE" in prompt
    assert "https://example.com" in prompt


def test_build_prompt_empty_data(monkeypatch):
    """Empty company_data falls back to 'No content available.'"""
    monkeypatch.setenv("DRY_RUN", "false")
    from agents.signal_extractor import SignalExtractorAgent

    agent = SignalExtractorAgent()
    prompt = agent._build_prompt({})

    assert "No content available." in prompt
