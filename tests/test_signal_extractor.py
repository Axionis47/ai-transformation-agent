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


def test_build_prompt_list_job_postings_labelled(monkeypatch):
    """Job postings as a list are labelled [JOB POSTING 1], [JOB POSTING 2], etc."""
    monkeypatch.setenv("DRY_RUN", "false")
    from agents.signal_extractor import SignalExtractorAgent

    agent = SignalExtractorAgent()
    company_data = {
        "url": "https://example.com",
        "job_postings": ["Data Engineer — BigQuery", "ML Engineer — PyTorch"],
    }
    prompt = agent._build_prompt(company_data)

    assert "[JOB POSTING 1]" in prompt
    assert "[JOB POSTING 2]" in prompt
    assert "Data Engineer" in prompt
    assert "ML Engineer" in prompt


def test_build_prompt_string_job_postings_backward_compat(monkeypatch):
    """Job postings as a plain string are still included without numbered labels."""
    monkeypatch.setenv("DRY_RUN", "false")
    from agents.signal_extractor import SignalExtractorAgent

    agent = SignalExtractorAgent()
    company_data = {
        "url": "https://example.com",
        "job_postings": "We are hiring a backend engineer.",
    }
    prompt = agent._build_prompt(company_data)

    assert "JOB POSTINGS" in prompt
    assert "backend engineer" in prompt
    assert "[JOB POSTING 1]" not in prompt


def test_build_prompt_includes_blog_section(monkeypatch):
    """_build_prompt includes BLOG / PRESS section when blog_text is present."""
    monkeypatch.setenv("DRY_RUN", "false")
    from agents.signal_extractor import SignalExtractorAgent

    agent = SignalExtractorAgent()
    company_data = {
        "url": "https://example.com",
        "blog_text": "We raised Series B to accelerate our AI roadmap.",
    }
    prompt = agent._build_prompt(company_data)

    assert "BLOG / PRESS" in prompt
    assert "Series B" in prompt


def test_build_prompt_includes_team_section(monkeypatch):
    """_build_prompt includes TEAM PAGE section when team_text is present."""
    monkeypatch.setenv("DRY_RUN", "false")
    from agents.signal_extractor import SignalExtractorAgent

    agent = SignalExtractorAgent()
    company_data = {
        "url": "https://example.com",
        "team_text": "VP of Engineering, Head of Product, 3 Data Analysts",
    }
    prompt = agent._build_prompt(company_data)

    assert "TEAM PAGE" in prompt
    assert "VP of Engineering" in prompt


def test_rank_and_budget_caps_at_max(monkeypatch):
    """_rank_and_budget returns at most max_signals items from a larger input."""
    monkeypatch.setenv("DRY_RUN", "false")
    from agents.signal_extractor import SignalExtractorAgent

    agent = SignalExtractorAgent()
    signals = [
        {"type": "tech_stack", "value": f"Tool-{i}", "confidence": 0.9}
        for i in range(30)
    ]
    result = agent._rank_and_budget(signals, max_signals=25)

    assert len(result) == 25


def test_rank_and_budget_priority_order(monkeypatch):
    """pain_point signals rank above tech_stack signals regardless of input order."""
    monkeypatch.setenv("DRY_RUN", "false")
    from agents.signal_extractor import SignalExtractorAgent

    agent = SignalExtractorAgent()
    signals = [
        {"type": "tech_stack", "value": "Kubernetes", "confidence": 1.0},
        {"type": "pain_point", "value": "manual reconciliation", "confidence": 0.7},
        {"type": "industry_hint", "value": "fintech", "confidence": 0.95},
    ]
    result = agent._rank_and_budget(signals)

    types = [s["type"] for s in result]
    assert types[0] == "pain_point", f"Expected pain_point first, got {types}"
    assert types[-1] == "industry_hint", f"Expected industry_hint last, got {types}"


def test_rank_and_budget_dedup_keeps_higher_confidence(monkeypatch):
    """Duplicate type+value entries keep the one with higher confidence."""
    monkeypatch.setenv("DRY_RUN", "false")
    from agents.signal_extractor import SignalExtractorAgent

    agent = SignalExtractorAgent()
    signals = [
        {"type": "tech_stack", "value": "BigQuery", "confidence": 0.6},
        {"type": "tech_stack", "value": "BigQuery", "confidence": 0.95},
    ]
    result = agent._rank_and_budget(signals)

    bq = [s for s in result if s["value"] == "BigQuery"]
    assert len(bq) == 1, "Duplicate should be deduped to one entry"
    assert bq[0]["confidence"] == 0.95, "Should keep higher confidence"


def test_fixtures_have_blog_and_team_signals():
    """All sample_signals fixtures contain at least one blog and one team_page source."""
    import json
    from pathlib import Path

    fixtures_dir = Path(__file__).resolve().parent / "fixtures"
    fixture_files = list(fixtures_dir.glob("sample_signals*.json"))
    assert fixture_files, "No sample_signals fixtures found"

    for fixture_path in fixture_files:
        data = json.loads(fixture_path.read_text())
        sources = {s["source"] for s in data["signals"]}
        assert "blog" in sources, f"{fixture_path.name}: missing blog source signal"
        assert "team_page" in sources, f"{fixture_path.name}: missing team_page source signal"
        types = {s["type"] for s in data["signals"]}
        assert "org_signal" in types, f"{fixture_path.name}: missing org_signal type"
        assert len(data["signals"]) <= 25, f"{fixture_path.name}: signal count exceeds budget of 25"
