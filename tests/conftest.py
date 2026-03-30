"""Shared test fixtures — isolates RAGStore singleton to prevent SQLite locking."""

import os

import pytest

import services.rag.store as store_module


def pytest_collection_modifyitems(config, items):
    """Skip tests marked requires_gcp when no GCP credentials are available."""
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or os.environ.get("GOOGLE_CLOUD_PROJECT"):
        return
    skip_gcp = pytest.mark.skip(reason="No GCP credentials — skipping API test")
    for item in items:
        if "requires_gcp" in item.keywords:
            item.add_marker(skip_gcp)


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
