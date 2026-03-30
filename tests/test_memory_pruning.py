"""Tests for services/memory/pruning.py — evidence pruning utilities."""

from core.schemas import EvidenceItem, EvidenceSource
from services.memory.pruning import (
    deduplicate_by_source,
    prune_by_relevance,
    prune_for_field_scope,
)


def _item(eid: str, score: float = 0.5, source_ref: str = "", title: str = "", snippet: str = "") -> EvidenceItem:
    return EvidenceItem(
        evidence_id=eid,
        run_id="r1",
        source_type=EvidenceSource.WINS_KB,
        source_ref=source_ref or eid,
        title=title or f"Title {eid}",
        snippet=snippet or f"Snippet {eid}",
        relevance_score=score,
    )


def test_prune_by_relevance_drops_low():
    items = [_item("e1", 0.9), _item("e2", 0.1), _item("e3", 0.5)]
    kept, dropped = prune_by_relevance(items, min_relevance=0.4, max_items=10)
    assert len(kept) == 2
    assert dropped == 1
    assert all(e.relevance_score >= 0.4 for e in kept)


def test_prune_by_relevance_caps_max():
    items = [_item(f"e{i}", 0.5 + i * 0.01) for i in range(10)]
    kept, dropped = prune_by_relevance(items, min_relevance=0.0, max_items=3)
    assert len(kept) == 3
    assert dropped == 7
    # Highest scores kept
    assert kept[0].relevance_score >= kept[1].relevance_score


def test_prune_by_relevance_empty():
    kept, dropped = prune_by_relevance([], min_relevance=0.5, max_items=10)
    assert kept == []
    assert dropped == 0


def test_prune_for_field_scope_filters():
    items = [
        _item("e1", snippet="The company provides excellent services"),
        _item("e2", snippet="Revenue grew 40% last year from subscriptions"),
        _item("e3", snippet="The workflow is manual and slow"),
    ]
    keywords = {
        "company_profile": ["company", "provides", "services"],
        "business_model": ["revenue", "subscription"],
    }
    result = prune_for_field_scope(items, keywords, ["company_profile"], max_per_field=5)
    assert len(result) == 1
    assert result[0].evidence_id == "e1"


def test_prune_for_field_scope_multiple_fields():
    items = [
        _item("e1", snippet="The company provides services"),
        _item("e2", snippet="Revenue from subscriptions"),
        _item("e3", snippet="unrelated text nothing here"),
    ]
    keywords = {
        "company_profile": ["company", "provides"],
        "business_model": ["revenue", "subscription"],
    }
    result = prune_for_field_scope(items, keywords, ["company_profile", "business_model"])
    assert len(result) == 2


def test_prune_for_field_scope_max_per_field():
    items = [_item(f"e{i}", snippet=f"company info {i}") for i in range(10)]
    keywords = {"company_profile": ["company"]}
    result = prune_for_field_scope(items, keywords, ["company_profile"], max_per_field=3)
    assert len(result) == 3


def test_deduplicate_by_source_keeps_highest():
    items = [
        _item("e1", score=0.3, source_ref="src1"),
        _item("e2", score=0.9, source_ref="src1"),
        _item("e3", score=0.5, source_ref="src2"),
    ]
    result = deduplicate_by_source(items)
    assert len(result) == 2
    src1_item = [e for e in result if e.source_ref == "src1"][0]
    assert src1_item.relevance_score == 0.9


def test_deduplicate_preserves_unique_sources():
    items = [_item(f"e{i}", source_ref=f"src{i}") for i in range(5)]
    result = deduplicate_by_source(items)
    assert len(result) == 5
