"""Tests for engines/thought/evidence_acc.py -- EvidenceAccumulator."""
from __future__ import annotations
import uuid
from core.schemas import EvidenceItem, EvidenceSource
from engines.thought.evidence_acc import EvidenceAccumulator


def _item(ref: str, rel: float = 0.7) -> EvidenceItem:
    return EvidenceItem(evidence_id=str(uuid.uuid4()), run_id="r",
        source_type=EvidenceSource.GOOGLE_SEARCH, source_ref=ref,
        title="T", snippet="snippet", relevance_score=rel)


def test_add_new_evidence():
    acc = EvidenceAccumulator()
    assert acc.add(_item("ref-001")) is True
    assert acc.count() == 1


def test_dedup_by_source_ref():
    acc = EvidenceAccumulator()
    acc.add(_item("ref-dup", 0.5))
    assert acc.add(_item("ref-dup", 0.4)) is False
    assert acc.count() == 1


def test_higher_score_replaces():
    acc = EvidenceAccumulator()
    acc.add(_item("ref-x", 0.4))
    acc.add(_item("ref-x", 0.9))
    assert acc.get_all()[0].relevance_score == 0.9


def test_get_all_sorted_by_relevance():
    acc = EvidenceAccumulator()
    for ref, rel in [("a", 0.3), ("b", 0.9), ("c", 0.6)]:
        acc.add(_item(ref, rel))
    scores = [i.relevance_score for i in acc.get_all()]
    assert scores == sorted(scores, reverse=True)


def test_source_types_unique():
    acc = EvidenceAccumulator()
    acc.add(_item("ref-gs"))
    acc.add(EvidenceItem(evidence_id=str(uuid.uuid4()), run_id="r",
        source_type=EvidenceSource.WINS_KB, source_ref="ref-kb",
        title="KB", snippet="kb snippet", relevance_score=0.7))
    types = acc.source_types()
    assert EvidenceSource.GOOGLE_SEARCH.value in types
    assert EvidenceSource.WINS_KB.value in types


def test_count_tracks_correctly():
    acc = EvidenceAccumulator()
    for i in range(5):
        acc.add(_item(f"ref-{i}"))
    assert acc.count() == 5
    acc.add(_item("ref-0"))
    assert acc.count() == 5
