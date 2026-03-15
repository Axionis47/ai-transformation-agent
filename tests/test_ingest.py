"""Tests for rag/ingest.py — seed loading, idempotency, and dry-run skip."""

import os


def test_ingest_loads_seeds(monkeypatch, tmp_path):
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path))
    monkeypatch.delenv("DRY_RUN", raising=False)

    from rag.ingest import ensure_seeds_loaded
    from rag.vector_store import ChromaStore

    ensure_seeds_loaded()

    store = ChromaStore()
    store._init_chroma()
    assert store._collection.count() == 20


def test_ingest_idempotent(monkeypatch, tmp_path):
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path))
    monkeypatch.delenv("DRY_RUN", raising=False)

    from rag.ingest import ensure_seeds_loaded
    from rag.vector_store import ChromaStore

    ensure_seeds_loaded()
    ensure_seeds_loaded()  # second call — must not raise

    store = ChromaStore()
    store._init_chroma()
    assert store._collection.count() == 20


def test_ingest_skips_dry_run(monkeypatch, tmp_path):
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path))

    import chromadb

    called = []
    original_persistent = chromadb.PersistentClient

    def mock_persistent(*args, **kwargs):
        called.append(True)
        return original_persistent(*args, **kwargs)

    monkeypatch.setattr(chromadb, "PersistentClient", mock_persistent)

    from rag.ingest import ensure_seeds_loaded

    ensure_seeds_loaded()

    assert len(called) == 0, "ChromaDB should not be called in dry-run mode"
