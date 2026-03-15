"""RAG ingest — loads seed data into ChromaDB at startup."""

from __future__ import annotations

import json
import os
from pathlib import Path

_SEEDS_PATH = (
    Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "rag_seeds" / "seeds.json"
)
_SEED_COUNT = 10


def ensure_seeds_loaded() -> None:
    """Upsert seed documents into ChromaDB — idempotent, skips if already loaded."""
    if os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes"):
        return  # MockStore handles dry-run; no ChromaDB needed

    from rag.vector_store import ChromaStore  # local import avoids circular at module level

    store = ChromaStore()
    store._init_chroma()

    if store._collection.count() >= _SEED_COUNT:
        return  # Already seeded — nothing to do

    seeds = json.loads(_SEEDS_PATH.read_text())
    ids = [s["id"] for s in seeds]
    documents = [s["text"] for s in seeds]
    metadatas = [
        {k: v for k, v in s.items() if k not in ("id", "text")} for s in seeds
    ]
    store._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)


if __name__ == "__main__":
    ensure_seeds_loaded()
    print(f"Seeds loaded from {_SEEDS_PATH}")
