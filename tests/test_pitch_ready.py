"""Tests for question engine, readiness score, PitchBriefAgent, and pipeline Stage 8."""

from __future__ import annotations

import pytest

from agents.base import AgentError
from agents.pitch_brief import PitchBriefAgent
from orchestrator.pipeline import run_pipeline
from orchestrator.question_engine import generate_questions
from orchestrator.readiness import compute_readiness
from orchestrator.state import PipelineStatus


# --- question engine ---

def test_generate_questions_generic_when_no_matches():
    questions = generate_questions({}, {})
    assert len(questions) == 3
    for q in questions:
        assert "question" in q
        assert "dimension" in q
        assert "potential_lift" in q


def test_generate_questions_gap_below_threshold():
    match_results = {
        "delivered": [
            {
                "confidence": 0.8,
                "confidence_breakdown": {
                    "pain_point_match": 0.3,
                    "tech_feasibility": 0.4,
                    "scale_match": 0.7,
                    "maturity_fit": 0.8,
                    "evidence_depth": 0.2,
                },
            }
        ]
    }
    questions = generate_questions(match_results, {})
    assert len(questions) == 3
    dims = [q["dimension"] for q in questions]
    assert "pain_point_match" in dims
    assert "tech_feasibility" in dims
    assert "evidence_depth" in dims


def test_generate_questions_sorted_by_lift():
    match_results = {
        "delivered": [
            {
                "confidence_breakdown": {
                    "pain_point_match": 0.1,
                    "tech_feasibility": 0.1,
                    "evidence_depth": 0.1,
                }
            }
        ]
    }
    questions = generate_questions(match_results, {})
    lifts = [q["potential_lift"] for q in questions]
    assert lifts == sorted(lifts, reverse=True)


def test_generate_questions_skips_industry_match():
    match_results = {
        "delivered": [
            {
                "confidence_breakdown": {"industry_match": 0.1}
            }
        ]
    }
    questions = generate_questions(match_results, {})
    dims = [q["dimension"] for q in questions]
    assert "industry_match" not in dims


# --- readiness score ---

def test_readiness_empty_inputs():
    r = compute_readiness({}, {}, False)
    assert "score" in r
    assert "label" in r
    assert "components" in r
    assert "next_action" in r
    assert 0.0 <= r["score"] <= 1.0


def test_readiness_high_confidence():
    signals = {
        "signals": [{"type": "pain_point", "source": "user_hint"}] * 12
    }
    match_results = {
        "delivered": [
            {
                "confidence": 0.95,
                "proven_metrics": {"primary_value": "30%", "primary_label": "cost reduction"},
            }
        ]
    }
    r = compute_readiness(signals, match_results, True)
    assert r["score"] >= 0.90
    assert r["label"] == "High confidence"


def test_readiness_components_sum_weighted():
    signals = {"signals": [{"type": "pain_point", "source": "about_text"}] * 5}
    match_results = {"delivered": [{"confidence": 0.6}]}
    r = compute_readiness(signals, match_results, False)
    comps = r["components"]
    expected = (
        comps["signal_completeness"] * 0.20
        + comps["match_confidence"] * 0.30
        + comps["pain_confirmation"] * 0.25
        + comps["roi_specificity"] * 0.25
    )
    assert abs(r["score"] - round(expected, 3)) < 0.001


# --- PitchBriefAgent ---

def test_pitch_brief_dry_run_returns_all_keys(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    agent = PitchBriefAgent()
    result = agent.run({
        "signals": {"signals": [{"type": "pain_point", "value": "manual ops", "source": "about_text"}]},
        "match_results": {"delivered": [{"confidence": 0.8, "source_title": "Win A",
                                         "tech_approach": "ML pipeline", "engagement_duration": 5,
                                         "proven_metrics": {"primary_label": "cost down", "primary_value": "20%"},
                                         "client_profile_summary": "mid-market SaaS"}]},
        "use_cases": [{"tier": "LOW_HANGING_FRUIT", "title": "Automation", "roi_estimate": "20% cost cut"}],
    })
    assert not isinstance(result, AgentError)
    for key in ["opening_line", "story", "roi_conversation", "questions", "objection_prep"]:
        assert key in result, f"Missing key: {key}"


def test_pitch_brief_dry_run_empty_inputs(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    agent = PitchBriefAgent()
    result = agent.run({})
    assert not isinstance(result, AgentError)
    assert "opening_line" in result


def test_pitch_brief_parse_response_invalid_json():
    agent = PitchBriefAgent()
    result = agent._parse_response("not json at all {broken")
    assert isinstance(result, AgentError)
    assert result.code == "PARSE_FAIL"


def test_pitch_brief_parse_response_missing_key():
    import json
    agent = PitchBriefAgent()
    partial = json.dumps({"opening_line": "Hi", "story": "story"})
    result = agent._parse_response(partial)
    assert isinstance(result, AgentError)
    assert result.code == "INCOMPLETE_BRIEF"


# --- pipeline Stage 8 integration ---

def test_dry_run_pipeline_includes_stage8(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    state = run_pipeline(url="https://example.com", dry_run=True)
    assert state.status == PipelineStatus.COMPLETE
    assert state.pitch_brief is not None
    assert state.readiness is not None
    assert state.suggested_questions is not None


def test_dry_run_pitch_brief_has_all_sections(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    state = run_pipeline(url="https://example.com", dry_run=True)
    brief = state.pitch_brief
    for key in ["opening_line", "story", "roi_conversation", "questions", "objection_prep"]:
        assert key in brief, f"pitch_brief missing: {key}"


def test_dry_run_readiness_valid_score(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    state = run_pipeline(url="https://example.com", dry_run=True)
    assert 0.0 <= state.readiness["score"] <= 1.0
    assert "label" in state.readiness
    assert "components" in state.readiness
    assert "next_action" in state.readiness


def test_dry_run_questions_list(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    state = run_pipeline(url="https://example.com", dry_run=True)
    assert isinstance(state.suggested_questions, list)
    assert len(state.suggested_questions) <= 3
    for q in state.suggested_questions:
        assert "question" in q
