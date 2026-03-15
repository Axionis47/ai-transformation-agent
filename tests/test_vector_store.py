"""Tests for rag/vector_store.py — MockStore and ChromaStore."""

import tempfile
import os

from rag.vector_store import ChromaStore, MockStore, get_vector_store


def test_mock_store_query_returns_list():
    store = MockStore()
    results = store.query("AI transformation", k=2)
    assert isinstance(results, list)
    assert len(results) > 0


def test_mock_store_add_is_noop():
    store = MockStore()
    result = store.add([{"id": "1", "text": "test"}])
    assert result is None


def test_dry_run_factory_returns_mock(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    store = get_vector_store()
    assert isinstance(store, MockStore)


def test_chroma_store_add_and_query():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["CHROMA_PERSIST_DIR"] = tmpdir
        store = ChromaStore()
        store._persist_dir = tmpdir

        add_result = store.add([
            {"id": "doc1", "text": "AI-powered logistics route optimization"},
            {"id": "doc2", "text": "Machine learning for demand forecasting"},
        ])
        assert add_result is None

        results = store.query("logistics AI", k=1)
        assert isinstance(results, list)
        assert len(results) == 1
        assert "logistics" in results[0]["text"].lower()
