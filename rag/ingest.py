"""RAG ingest — loads victory data into ChromaDB at startup."""

from __future__ import annotations

import json
import os
from pathlib import Path

_FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "rag_seeds"
_VICTORIES_PATH = _FIXTURES / "victories.json"
_SEEDS_FALLBACK = _FIXTURES / "seeds.json"
_SEED_COUNT = 20


def _load_victories() -> tuple[list[str], list[str], list[dict]]:
    """Load victories.json and return (ids, documents, metadatas) for ChromaDB upsert."""
    if _VICTORIES_PATH.exists():
        records = json.loads(_VICTORIES_PATH.read_text())
        ids = [r["id"] for r in records]
        documents = [r["embed_text"] for r in records]
        metadatas = [
            {
                "industry": r["industry"],
                "size_label": r["company_profile"]["size_label"],
                "engagement_title": r["engagement_title"],
                "primary_metric_label": r["results"]["primary_metric"]["label"],
                "primary_metric_value": r["results"]["primary_metric"]["value"],
                "measurement_period": r["results"]["measurement_period"],
                "duration_months": r["engagement_details"]["duration_months"],
                "maturity_at_engagement": r.get("maturity_at_engagement", ""),
            }
            for r in records
        ]
        return ids, documents, metadatas

    # Fallback to legacy seeds.json
    seeds = json.loads(_SEEDS_FALLBACK.read_text())
    ids = [s["id"] for s in seeds]
    documents = [s["text"] for s in seeds]
    metadatas = [{k: v for k, v in s.items() if k not in ("id", "text")} for s in seeds]
    return ids, documents, metadatas


def ensure_seeds_loaded() -> None:
    """Upsert victory documents into ChromaDB — idempotent, skips if already loaded."""
    if os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes"):
        return  # MockStore handles dry-run; no ChromaDB needed

    from rag.vector_store import ChromaStore  # local import avoids circular at module level

    store = ChromaStore()
    store._init_chroma()

    if store._collection.count() >= _SEED_COUNT:
        return  # Already seeded — nothing to do

    ids, documents, metadatas = _load_victories()
    store._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)


if __name__ == "__main__":
    ensure_seeds_loaded()
    source = _VICTORIES_PATH if _VICTORIES_PATH.exists() else _SEEDS_FALLBACK
    print(f"Seeds loaded from {source}")
