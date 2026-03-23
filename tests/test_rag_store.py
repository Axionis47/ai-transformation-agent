"""Tests for services/rag/store.py — ChromaDB wrapper."""
import tempfile

import pytest

from services.rag.store import RAGStore


@pytest.fixture
def store():
    """Isolated RAGStore using a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield RAGStore(persist_dir=tmpdir)


def _doc(doc_id: str, text: str, extra_meta: dict | None = None) -> dict:
    """Build a valid doc dict — ChromaDB requires non-empty metadata."""
    meta = {"source": "test"}
    if extra_meta:
        meta.update(extra_meta)
    return {"id": doc_id, "text": text, "metadata": meta}


def test_store_initializes(store):
    assert store is not None


def test_initial_count_is_zero(store):
    assert store.count() == 0


def test_add_documents_returns_count(store):
    docs = [
        _doc("doc-1", "Customer support automation", {"industry": "finance"}),
        _doc("doc-2", "Fraud detection copilot", {"industry": "finance"}),
    ]
    added = store.add_documents(docs)
    assert added == 2


def test_count_reflects_added_documents(store):
    docs = [
        _doc("doc-a", "Logistics dispatch optimization"),
        _doc("doc-b", "Predictive maintenance manufacturing"),
        _doc("doc-c", "Patient scheduling healthcare"),
    ]
    store.add_documents(docs)
    assert store.count() == 3


def test_query_returns_results(store):
    store.add_documents([
        _doc("eng-001", "Customer support triage automation for financial services.", {"title": "Triage"}),
    ])
    results = store.query("customer support", top_k=5)
    assert len(results) >= 1


def test_query_results_have_required_fields(store):
    store.add_documents([
        _doc("eng-002", "Fraud detection copilot for analysts.", {"title": "Fraud"}),
    ])
    results = store.query("fraud detection")
    assert len(results) > 0
    r = results[0]
    assert "id" in r
    assert "text" in r
    assert "metadata" in r
    assert "score" in r


def test_query_score_is_between_0_and_1(store):
    store.add_documents([
        _doc("eng-003", "Inventory forecasting for retail chains."),
    ])
    results = store.query("inventory management retail")
    for r in results:
        assert 0.0 <= r["score"] <= 1.0


def test_query_top_k_limits_results(store):
    docs = [
        _doc(f"doc-{i}", f"Engagement document number {i} about automation.")
        for i in range(10)
    ]
    store.add_documents(docs)
    results = store.query("automation", top_k=3)
    assert len(results) <= 3


def test_query_returns_sorted_by_relevance(store):
    store.add_documents([
        _doc("rel-1", "Customer support triage and ticket automation."),
        _doc("rel-2", "Fleet maintenance scheduling for trucks."),
    ])
    results = store.query("customer support ticket triage")
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_clear_empties_collection(store):
    store.add_documents([_doc("doc-x", "Some document text here.")])
    assert store.count() == 1
    store.clear()
    assert store.count() == 0


def test_add_after_clear_works(store):
    store.add_documents([_doc("doc-y", "Post-clear document.")])
    store.clear()
    store.add_documents([_doc("doc-y", "Post-clear document.")])
    assert store.count() == 1


def test_add_documents_upserts_on_duplicate_id(store):
    doc = _doc("dup-1", "Original text for dedup test.")
    store.add_documents([doc])
    store.add_documents([doc])  # same id — upsert
    assert store.count() == 1
