"""End-to-end pipeline tests for user hints integration."""
from __future__ import annotations

import pytest

from orchestrator.pipeline import run_pipeline
from orchestrator.state import PipelineStatus


def _run(hints: dict | None = None) -> object:
    return run_pipeline(url="https://example.com", dry_run=True, user_hints=hints)


def test_pipeline_completes_without_hints():
    state = _run()
    assert state.status == PipelineStatus.COMPLETE
    assert state.has_user_hints is False


def test_pipeline_completes_with_hints():
    hints = {
        "pain_points": ["manual route planning is slow and expensive"],
        "known_tech": ["BigQuery"],
        "industry": "logistics",
    }
    state = _run(hints)
    assert state.status == PipelineStatus.COMPLETE
    assert state.has_user_hints is True


def test_hints_stored_on_state():
    hints = {
        "pain_points": ["manual route planning is slow and expensive"],
        "known_tech": ["BigQuery"],
        "industry": "logistics",
    }
    state = _run(hints)
    assert state.user_hints is not None
    assert state.user_hints.get("industry") == "logistics"


def test_invalid_hints_do_not_crash_pipeline():
    # industry value not in known list — hints should be silently dropped
    state = _run({"industry": "martian_mining"})
    assert state.status == PipelineStatus.COMPLETE
    assert state.has_user_hints is False


def test_hint_signals_present_in_merged_signals():
    hints = {
        "pain_points": ["manual route planning is slow and expensive"],
        "known_tech": ["BigQuery"],
        "industry": "logistics",
    }
    state = _run(hints)
    assert state.signals is not None
    sources = {s.get("source") for s in state.signals.get("signals", [])}
    assert "user_hint" in sources


def test_hints_set_evidence_ceiling_to_url_plus_hints():
    hints = {
        "pain_points": ["manual route planning is slow and expensive"],
        "known_tech": ["BigQuery"],
        "industry": "logistics",
    }
    state = _run(hints)
    assert state.match_results is not None
    delivered = state.match_results.get("delivered", [])
    if delivered:
        cb = delivered[0].get("confidence_breakdown")
        if cb:
            assert cb.get("evidence_ceiling") == "url_plus_hints"
