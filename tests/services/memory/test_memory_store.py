"""Tests for services/memory/store.py — EvidenceStore."""

from core.schemas import EvidenceItem, EvidenceSource
from services.memory.store import EvidenceStore


def _item(eid: str, run_id: str = "r1", score: float = 0.5, source_ref: str = "") -> EvidenceItem:
    return EvidenceItem(
        evidence_id=eid,
        run_id=run_id,
        source_type=EvidenceSource.WINS_KB,
        source_ref=source_ref or eid,
        title=f"Title {eid}",
        snippet=f"Snippet {eid}",
        relevance_score=score,
    )


def test_add_and_get_all():
    store = EvidenceStore()
    store.add("r1", _item("e1", score=0.8))
    store.add("r1", _item("e2", score=0.6))
    items = store.get_all("r1")
    assert len(items) == 2
    assert items[0].evidence_id == "e1"  # higher score first


def test_add_duplicate_keeps_higher_score():
    store = EvidenceStore()
    store.add("r1", _item("e1", score=0.5))
    store.add("r1", _item("e1", score=0.9))
    items = store.get_all("r1")
    assert len(items) == 1
    assert items[0].relevance_score == 0.9


def test_get_by_ids():
    store = EvidenceStore()
    store.add("r1", _item("e1"))
    store.add("r1", _item("e2"))
    store.add("r1", _item("e3"))
    result = store.get_by_ids("r1", ["e1", "e3"])
    assert len(result) == 2
    assert {e.evidence_id for e in result} == {"e1", "e3"}


def test_get_filtered_by_relevance():
    store = EvidenceStore()
    store.add("r1", _item("e1", score=0.9))
    store.add("r1", _item("e2", score=0.1))
    store.add("r1", _item("e3", score=0.5))
    items, dropped = store.get_filtered("r1", min_relevance=0.4)
    assert len(items) == 2
    assert dropped == 1


def test_get_filtered_respects_max_items():
    store = EvidenceStore()
    for i in range(10):
        store.add("r1", _item(f"e{i}", score=0.5 + i * 0.01))
    items, dropped = store.get_filtered("r1", max_items=3)
    assert len(items) == 3
    assert dropped == 7


def test_get_filtered_by_source_type():
    store = EvidenceStore()
    e1 = _item("e1")
    e2 = EvidenceItem(
        evidence_id="e2",
        run_id="r1",
        source_type=EvidenceSource.GOOGLE_SEARCH,
        source_ref="e2",
        title="T",
        snippet="S",
        relevance_score=0.8,
    )
    store.add("r1", e1)
    store.add("r1", e2)
    items, _ = store.get_filtered("r1", source_types=["google_search"])
    assert len(items) == 1
    assert items[0].source_type == EvidenceSource.GOOGLE_SEARCH


def test_prune_removes_low_relevance():
    store = EvidenceStore()
    store.add("r1", _item("e1", score=0.9))
    store.add("r1", _item("e2", score=0.1))
    store.add("r1", _item("e3", score=0.5))
    pruned = store.prune("r1", min_relevance=0.4, max_items=10)
    assert pruned == 1
    assert store.count("r1") == 2


def test_prune_caps_at_max_items():
    store = EvidenceStore()
    for i in range(10):
        store.add("r1", _item(f"e{i}", score=0.5 + i * 0.01))
    pruned = store.prune("r1", min_relevance=0.0, max_items=3)
    assert pruned == 7
    assert store.count("r1") == 3


def test_runs_are_isolated():
    store = EvidenceStore()
    store.add("r1", _item("e1", run_id="r1"))
    store.add("r2", _item("e2", run_id="r2"))
    assert store.count("r1") == 1
    assert store.count("r2") == 1
    assert store.get_all("r3") == []
