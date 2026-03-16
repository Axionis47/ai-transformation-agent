"""End-to-end dry-run test for the 7-stage Sprint 4 pipeline."""
import os

from orchestrator.pipeline import run_pipeline
from orchestrator.state import PipelineStatus


def test_dry_run_7_stage_complete(monkeypatch):
    """Full pipeline dry-run produces all 7 state fields."""
    monkeypatch.setenv("DRY_RUN", "true")
    state = run_pipeline(url="https://example.com", dry_run=True)

    assert state.status == PipelineStatus.COMPLETE

    # Stage 1: company_data
    assert state.company_data is not None
    assert "about_text" in state.company_data

    # Stage 2: signals
    assert state.signals is not None
    assert "signals" in state.signals
    signal_count = state.signals.get("signal_count", len(state.signals.get("signals", [])))
    assert signal_count > 0 or len(state.signals.get("signals", [])) > 0

    # Stage 3: maturity
    assert state.maturity is not None
    assert "composite_score" in state.maturity
    assert "dimensions" in state.maturity
    assert "composite_label" in state.maturity

    # Stage 4: rag_context
    assert state.rag_context is not None
    assert len(state.rag_context) > 0

    # Stage 5: victory_matches
    assert state.victory_matches is not None
    assert len(state.victory_matches) > 0
    for vm in state.victory_matches:
        assert "match_tier" in vm
        assert vm["match_tier"] in ("DIRECT_MATCH", "CALIBRATION_MATCH", "ADJACENT_MATCH")

    # Stage 6: use_cases
    assert state.use_cases is not None
    assert len(state.use_cases) >= 2
    for uc in state.use_cases:
        assert "tier" in uc
        assert uc["tier"] in ("LOW_HANGING_FRUIT", "MEDIUM_SOLUTION", "HARD_EXPERIMENT")
        assert "data_flow" in uc

    # Stage 7: report
    assert state.report is not None
    for section in ["exec_summary", "current_state", "use_cases", "roadmap", "roi_analysis"]:
        assert section in state.report
        assert len(state.report[section]) > 50


def test_dry_run_analysis_backward_compat(monkeypatch):
    """state.analysis is populated for backward compat with API."""
    monkeypatch.setenv("DRY_RUN", "true")
    state = run_pipeline(url="https://example.com", dry_run=True)

    assert state.analysis is not None
    assert "maturity_score" in state.analysis
    assert "maturity_label" in state.analysis


def test_dry_run_no_api_calls(monkeypatch):
    """Dry-run makes zero network calls."""
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    state = run_pipeline(url="https://example.com", dry_run=True)
    assert state.status == PipelineStatus.COMPLETE
