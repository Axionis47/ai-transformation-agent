"""Tests for honest_conversation in PitchBriefAgent and pipeline."""

from __future__ import annotations

import pytest

from agents.pitch_brief import PitchBriefAgent
from orchestrator.pipeline import run_pipeline
from orchestrator.state import PipelineStatus

_LESSONS = {
    "primary_challenge": "Document format diversity caused low accuracy",
    "risk_factors": ["data_quality", "change_management"],
    "timeline_reality": "Accuracy improved at month 4",
    "what_we_would_do_differently": "Audit document formats in week 1",
}


def test_build_honest_conversation_uses_challenge():
    hc = PitchBriefAgent()._build_honest_conversation(_LESSONS)
    assert "Document format diversity" in hc
    assert len(hc) > 30


def test_build_honest_conversation_none_returns_fallback():
    hc = PitchBriefAgent()._build_honest_conversation(None)
    assert "insufficient data" in hc.lower()


def test_build_honest_conversation_empty_dict_returns_fallback():
    hc = PitchBriefAgent()._build_honest_conversation({})
    assert "insufficient data" in hc.lower()


def test_pitch_brief_honest_conversation_present(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    result = PitchBriefAgent().run({
        "signals": {"signals": [{"type": "pain_point", "value": "manual ops", "source": "about_text"}]},
        "match_results": {"delivered": [{
            "confidence": 0.8, "source_title": "Invoice Win",
            "tech_approach": "LLM pipeline", "engagement_duration": 3,
            "proven_metrics": {"primary_label": "STP rate", "primary_value": "82%"},
            "client_profile_summary": "mid-market lender",
            "lessons_learned": _LESSONS,
        }]},
        "use_cases": [{"tier": "LOW_HANGING_FRUIT", "title": "AP Auto", "roi_estimate": "$340K/yr"}],
        "lessons_learned": _LESSONS,
    })
    assert "honest_conversation" in result
    assert len(result["honest_conversation"]) > 20


def test_pitch_brief_honest_conversation_fallback_on_empty(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    result = PitchBriefAgent().run({})
    assert "honest_conversation" in result
    assert "insufficient data" in result["honest_conversation"].lower()


def test_dry_run_pipeline_honest_conversation_present(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    state = run_pipeline(url="https://example.com", dry_run=True)
    assert state.status == PipelineStatus.COMPLETE
    brief = state.pitch_brief or {}
    assert "honest_conversation" in brief
    assert len(brief["honest_conversation"]) > 20


def test_dry_run_pipeline_honest_conversation_engagement_specific(monkeypatch):
    """Pipeline has real lessons_learned from victories — not a fallback."""
    monkeypatch.setenv("DRY_RUN", "true")
    state = run_pipeline(url="https://example.com", dry_run=True)
    hc = (state.pitch_brief or {}).get("honest_conversation", "")
    assert "In a similar engagement" in hc, f"Expected engagement content: {hc[:100]}"
