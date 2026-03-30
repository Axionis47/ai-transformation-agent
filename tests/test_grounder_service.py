"""Tests for services/grounder/grounder.py — budget enforcement and trace emission."""

from __future__ import annotations

import pytest

from core.schemas import BudgetState, EvidenceSource
from services.grounder.fake_client import FakeGeminiClient
from services.grounder.grounder import Grounder, GroundingResult
from services.trace import get_events

RUN_ID = "test-run-grounder"

CONFIG = {
    "budgets": {
        "external_search_query_budget": 5,
        "external_search_max_calls": 3,
    }
}


def _make_grounder(responses=None):
    client = FakeGeminiClient(responses=responses)
    return Grounder(client=client, config=CONFIG), client


def _fresh_state():
    return BudgetState()


def test_ground_returns_grounding_result():
    grounder, _ = _make_grounder()
    result = grounder.ground("What does Acme Corp do?", RUN_ID, _fresh_state())
    assert isinstance(result, GroundingResult)


def test_ground_returns_synthesized_text():
    grounder, _ = _make_grounder()
    result = grounder.ground("What does Acme Corp do?", RUN_ID, _fresh_state())
    assert len(result.text) > 0


def test_evidence_items_have_google_search_source():
    grounder, _ = _make_grounder()
    result = grounder.ground("What does Acme Corp do?", RUN_ID, _fresh_state())
    assert all(e.source_type == EvidenceSource.GOOGLE_SEARCH for e in result.evidence_items)


def test_evidence_items_have_uri_and_title():
    grounder, _ = _make_grounder()
    result = grounder.ground("What does Acme Corp do?", RUN_ID, _fresh_state())
    for item in result.evidence_items:
        assert item.uri is not None and item.uri != ""
        assert item.title != ""


def test_evidence_items_have_snippet_and_confidence():
    grounder, _ = _make_grounder()
    result = grounder.ground("What does Acme Corp do?", RUN_ID, _fresh_state())
    for item in result.evidence_items:
        assert item.snippet != ""
        assert item.confidence_score is not None


def test_budget_blocks_when_query_budget_exhausted():
    grounder, _ = _make_grounder()
    state = _fresh_state()
    state.external_search_queries_used = 5  # at limit
    result = grounder.ground("What does Acme Corp do?", RUN_ID, state)
    assert result.budget_exhausted is True
    assert result.coverage_gap is not None


def test_budget_blocks_when_call_limit_reached():
    grounder, _ = _make_grounder()
    state = _fresh_state()
    state.external_search_calls_used = 3  # at limit
    result = grounder.ground("What does Acme Corp do?", RUN_ID, state)
    assert result.budget_exhausted is True
    assert result.coverage_gap is not None


def test_budget_increments_queries_used_by_query_count():
    grounder, _ = _make_grounder()
    state = _fresh_state()
    grounder.ground("What does Acme Corp do?", RUN_ID, state)
    # default fake response has 2 search queries
    assert state.external_search_queries_used == 2


def test_budget_increments_calls_used_by_one():
    grounder, _ = _make_grounder()
    state = _fresh_state()
    grounder.ground("What does Acme Corp do?", RUN_ID, state)
    assert state.external_search_calls_used == 1


def test_trace_grounding_call_requested_emitted():
    grounder, _ = _make_grounder()
    state = _fresh_state()
    grounder.ground("What does Acme Corp do?", RUN_ID, state)
    events = [e for e in get_events(RUN_ID) if e.event_type == "GROUNDING_CALL_REQUESTED"]
    assert len(events) >= 1


def test_trace_grounding_call_completed_emitted():
    grounder, _ = _make_grounder()
    state = _fresh_state()
    grounder.ground("What does Acme Corp do?", RUN_ID, state)
    events = [e for e in get_events(RUN_ID) if e.event_type == "GROUNDING_CALL_COMPLETED"]
    assert len(events) >= 1


def test_trace_queries_counted_emitted():
    grounder, _ = _make_grounder()
    state = _fresh_state()
    grounder.ground("What does Acme Corp do?", RUN_ID, state)
    events = [e for e in get_events(RUN_ID) if e.event_type == "GROUNDING_QUERIES_COUNTED"]
    assert len(events) >= 1


def test_coverage_gap_returned_when_budget_exhausted():
    grounder, _ = _make_grounder()
    state = _fresh_state()
    state.external_search_queries_used = 5
    result = grounder.ground("What does Acme Corp do?", RUN_ID, state)
    assert result.coverage_gap == "search query budget exhausted"
