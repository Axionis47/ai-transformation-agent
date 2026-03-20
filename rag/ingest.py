"""RAG ingest — loads victory data into ChromaDB at startup."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

_FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "rag_seeds"
_VICTORIES_PATH = _FIXTURES / "victories.json"
_SEEDS_FALLBACK = _FIXTURES / "seeds.json"
_INDUSTRY_CASES_PATH = _FIXTURES / "industry_cases.json"
_SEED_COUNT = 12
_INDUSTRY_SEED_COUNT = 5
_COLLECTION = "tenex_delivered"
_INDUSTRY_COLLECTION = "industry_cases"

logger = logging.getLogger(__name__)


def _load_victories() -> tuple[list[str], list[str], list[dict]]:
    """Load victories.json, validate through SolutionSchema, return (ids, documents, metadatas)."""
    from rag.schemas import SolutionSchema
    from pydantic import ValidationError

    if _VICTORIES_PATH.exists():
        raw_records = json.loads(_VICTORIES_PATH.read_text())
        ids, documents, metadatas = [], [], []
        for r in raw_records:
            try:
                SolutionSchema.model_validate(r)
            except ValidationError as exc:
                logger.warning("Skipping %s — validation warning: %s", r.get("id"), exc)
            ids.append(r["id"])
            documents.append(r["embed_text"])
            metadatas.append({
                "industry": r["industry"],
                "size_label": r["company_profile"]["size_label"],
                "engagement_title": r["engagement_title"],
                "primary_metric_label": r["results"]["primary_metric"]["label"],
                "primary_metric_value": r["results"]["primary_metric"]["value"],
                "measurement_period": r["results"]["measurement_period"],
                "duration_months": r["engagement_details"]["duration_months"],
                "maturity_at_engagement": r.get("maturity_at_engagement", ""),
            })
        return ids, documents, metadatas

    # Fallback to legacy seeds.json
    seeds = json.loads(_SEEDS_FALLBACK.read_text())
    ids = [s["id"] for s in seeds]
    documents = [s["text"] for s in seeds]
    metadatas = [{k: v for k, v in s.items() if k not in ("id", "text")} for s in seeds]
    return ids, documents, metadatas


def _load_industry_cases() -> tuple[list[str], list[str], list[dict]]:
    """Load industry_cases.json, validate, return (ids, documents, metadatas)."""
    from rag.schemas import IndustryCaseStudySchema
    from pydantic import ValidationError

    raw_records = json.loads(_INDUSTRY_CASES_PATH.read_text())
    ids, documents, metadatas = [], [], []
    for r in raw_records:
        try:
            IndustryCaseStudySchema.model_validate(r)
        except ValidationError as exc:
            logger.warning("Skipping %s — validation warning: %s", r.get("id"), exc)
        ids.append(r["id"])
        documents.append(r.get("embed_text", r.get("case_title", "")))
        metadatas.append({
            "industry": r["industry"],
            "company_name": r["company_profile"].get("company_name", ""),
            "use_case_category": r.get("use_case_category", ""),
            "maturity_signal": r.get("maturity_signal", ""),
            "status": r.get("status", "active"),
        })
    return ids, documents, metadatas


def ensure_seeds_loaded() -> None:
    """Upsert seed documents into both ChromaDB collections — idempotent."""
    if os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes"):
        return  # MockStore handles dry-run; no ChromaDB needed

    from rag.vector_store import ChromaStore  # local import avoids circular at module level

    # Library A: tenex_delivered
    store_a = ChromaStore(collection_name=_COLLECTION)
    store_a._init_chroma()
    if store_a._collection.count() < _SEED_COUNT:
        ids, documents, metadatas = _load_victories()
        store_a._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    # Library B: industry_cases
    if _INDUSTRY_CASES_PATH.exists():
        store_b = ChromaStore(collection_name=_INDUSTRY_COLLECTION)
        store_b._init_chroma()
        if store_b._collection.count() < _INDUSTRY_SEED_COUNT:
            ids, documents, metadatas = _load_industry_cases()
            store_b._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)


if __name__ == "__main__":
    ensure_seeds_loaded()
    source = _VICTORIES_PATH if _VICTORIES_PATH.exists() else _SEEDS_FALLBACK
    print(f"Seeds loaded from {source}")
