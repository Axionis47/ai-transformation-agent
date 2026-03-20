"""Tests for lessons_learned schema and fixture structure."""

from __future__ import annotations

import json
from pathlib import Path

from orchestrator.schemas import LessonsLearned
from rag.vector_store import MockStore

_VICTORIES = Path(__file__).parent / "fixtures" / "rag_seeds" / "victories.json"


# --- LessonsLearned schema ---

def test_lessons_learned_schema_valid():
    ll = LessonsLearned(
        primary_challenge="Test challenge",
        risk_factors=["risk_a", "risk_b"],
        timeline_reality="Month 3",
        what_we_would_do_differently="Start earlier",
    )
    assert ll.primary_challenge == "Test challenge"
    assert len(ll.risk_factors) == 2
    assert ll.timeline_reality == "Month 3"
    assert ll.what_we_would_do_differently == "Start earlier"


def test_lessons_learned_schema_defaults():
    ll = LessonsLearned()
    assert ll.primary_challenge == ""
    assert ll.risk_factors == []
    assert ll.timeline_reality == ""
    assert ll.what_we_would_do_differently == ""


# --- victories fixture structure ---

def test_all_victories_have_structured_lessons_learned():
    data = json.loads(_VICTORIES.read_text())
    for record in data:
        ll = record.get("lessons_learned")
        assert isinstance(ll, dict), f"{record['id']} missing structured lessons_learned"
        assert "primary_challenge" in ll, f"{record['id']} missing primary_challenge"
        assert "risk_factors" in ll, f"{record['id']} missing risk_factors"
        assert len(ll["risk_factors"]) >= 2, f"{record['id']} needs at least 2 risk_factors"


def test_victories_have_twelve_records():
    data = json.loads(_VICTORIES.read_text())
    assert len(data) == 12


# --- MockStore returns lessons_learned ---

def test_mock_store_query_all_includes_lessons_learned():
    store = MockStore()
    records = store.query_all()
    has_ll = sum(1 for r in records if isinstance(r.get("lessons_learned"), dict))
    assert has_ll == len(records), (
        f"Only {has_ll}/{len(records)} records have lessons_learned"
    )


def test_mock_store_query_returns_lessons_learned():
    store = MockStore()
    records = store.query("financial services invoice processing", k=3)
    for r in records:
        assert "lessons_learned" in r, f"{r.get('id')} missing lessons_learned in query"
        assert isinstance(r["lessons_learned"], dict)
