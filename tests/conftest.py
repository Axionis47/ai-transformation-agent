"""Shared test fixtures — isolates RAGStore singleton to prevent SQLite locking."""

import pytest

import services.rag.store as store_module
from services.rag.ingest import ensure_loaded
from services.rag.store import RAGStore


@pytest.fixture(autouse=True)
def isolate_rag_singleton(tmp_path):
    """Give each test a fresh RAGStore singleton backed by a temp directory.

    Prevents ChromaDB SQLite locking errors when multiple tests hit
    the default ./data/chroma_store concurrently. Tests that create
    their own RAGStore(persist_dir=...) are not affected — this only
    controls what get_rag_store() returns.
    """
    old = store_module._singleton
    store_module._singleton = RAGStore(persist_dir=str(tmp_path / "chroma"))
    yield store_module._singleton
    store_module._singleton = old
