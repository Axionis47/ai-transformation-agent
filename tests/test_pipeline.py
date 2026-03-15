"""Tests for orchestrator/pipeline.py — dry-run end-to-end."""

import os

from orchestrator.pipeline import run_pipeline
from orchestrator.state import PipelineStatus


def test_dry_run_completes(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    state = run_pipeline(url="https://example.com", dry_run=True)

    assert state.status == PipelineStatus.COMPLETE
    assert state.company_data is not None
    assert state.rag_context is not None
    assert state.analysis is not None
    assert state.report is not None

    # All 5 report sections present and non-empty
    for section in ["exec_summary", "current_state", "use_cases", "roadmap", "roi_analysis"]:
        assert section in state.report, f"Missing section: {section}"
        assert len(state.report[section]) > 100, f"Section too short: {section}"


def test_pipeline_state_transitions(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    state = run_pipeline(url="https://example.com", dry_run=True)

    # Should end in complete state
    assert state.status == PipelineStatus.COMPLETE
    assert state.error is None
    assert state.elapsed_seconds >= 0
    assert state.cost_usd == 0.0


def test_dry_run_no_real_api_calls(monkeypatch):
    """Ensure dry-run makes zero network calls by unsetting all credentials."""
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    state = run_pipeline(url="https://example.com", dry_run=True)
    assert state.status == PipelineStatus.COMPLETE
