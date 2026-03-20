"""Vector store abstraction — all RAG operations go through here."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from agents.base import AgentError

_INDUSTRY_KEYWORDS: dict[str, list[str]] = {
    "logistics": ["logistics", "freight", "shipping", "carrier", "supply chain", "warehouse"],
    "healthcare": ["health", "hospital", "clinic", "medical", "patient", "clinical", "ehr"],
    "financial_services": ["financial", "finance", "bank", "fintech", "lending", "compliance", "kyc"],
    "retail": ["retail", "ecommerce", "e-commerce", "shop", "consumer", "product catalog"],
    "insurance": ["insurance", "claims", "underwriting", "policy"],
    "professional_services": ["consulting", "professional services", "law firm", "advisory"],
    "manufacturing": ["manufacturing", "factory", "production", "industrial"],
    "energy": ["energy", "utility", "grid", "electric"],
    "real_estate": ["real estate", "proptech", "lease", "property"],
    "construction": ["construction", "equipment rental", "heavy equipment"],
    "ecommerce": ["ecommerce", "e-commerce", "online store", "product description", "catalog"],
}

_ADJACENT_INDUSTRIES: dict[str, set[str]] = {
    "logistics": {"manufacturing", "construction"},
    "manufacturing": {"logistics", "construction", "energy"},
    "healthcare": set(),
    "financial_services": {"insurance"},
    "insurance": {"financial_services"},
    "retail": {"ecommerce"},
    "ecommerce": {"retail"},
    "professional_services": {"real_estate"},
    "real_estate": {"professional_services"},
    "construction": {"manufacturing", "logistics"},
    "energy": {"manufacturing"},
}


def _detect_industry(text: str) -> str | None:
    """Return the best-matching industry key from query text, or None."""
    text_lower = text.lower()
    for industry, keywords in _INDUSTRY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return industry
    return None


def _filter_by_industry(records: list[dict], industry: str, k: int) -> list[dict]:
    """Return k records filtered to match industry, padded with remainder if needed."""
    adjacent = _ADJACENT_INDUSTRIES.get(industry, set())
    priority: list[dict] = []
    fallback: list[dict] = []
    for rec in records:
        rec_industry = rec.get("industry", "").lower()
        if rec_industry == industry:
            priority.append(rec)
        elif rec_industry in adjacent:
            priority.append(rec)
        else:
            fallback.append(rec)
    combined = priority + fallback
    return combined[:k]


class VectorStore(ABC):
    """Abstract interface for vector store backends."""

    @abstractmethod
    def add(self, docs: list[dict[str, Any]]) -> None | AgentError:
        """Add documents to the store."""
        ...

    @abstractmethod
    def query(self, text: str, k: int = 3) -> list[dict[str, Any]] | AgentError:
        """Query for similar documents."""
        ...


class ChromaStore(VectorStore):
    """ChromaDB-backed vector store with local persistence."""

    def __init__(self, collection_name: str = "tenex_delivered") -> None:
        self._persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./rag/store")
        self._collection_name = collection_name
        self._client = None
        self._collection = None

    def _init_chroma(self) -> None:
        if self._client is not None:
            return
        import chromadb  # noqa: local import

        Path(self._persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=self._persist_dir)
        self._collection = self._client.get_or_create_collection(self._collection_name)

    def add(self, docs: list[dict[str, Any]]) -> None | AgentError:
        try:
            self._init_chroma()
            ids = [doc.get("id", str(i)) for i, doc in enumerate(docs)]
            documents = [doc.get("text", json.dumps(doc)) for doc in docs]
            metadatas = [
                {k: v for k, v in doc.items() if k not in ("id", "text") and isinstance(v, (str, int, float, bool))}
                for doc in docs
            ]
            # ChromaDB rejects empty metadata dicts — only pass if non-empty
            has_metadata = any(m for m in metadatas)
            self._collection.add(
                ids=ids, documents=documents, metadatas=metadatas if has_metadata else None
            )
            return None
        except Exception as exc:
            return AgentError(
                code="VECTOR_ADD_FAIL",
                message=f"ChromaDB add error: {exc}",
                recoverable=True,
                agent_tag="RAG",
            )

    def query(self, text: str, k: int = 3) -> list[dict[str, Any]] | AgentError:
        try:
            self._init_chroma()
            results = self._collection.query(query_texts=[text], n_results=k)
            docs = []
            for i, doc_text in enumerate(results["documents"][0]):
                entry = {"text": doc_text}
                metas = results.get("metadatas") or []
                if metas and metas[0] and i < len(metas[0]) and metas[0][i]:
                    entry.update(metas[0][i])
                docs.append(entry)
            return docs
        except Exception as exc:
            return AgentError(
                code="VECTOR_QUERY_FAIL",
                message=f"ChromaDB query error: {exc}",
                recoverable=True,
                agent_tag="RAG",
            )


class MockStore(VectorStore):
    """Returns fixture data for dry-run mode — zero external calls."""

    _FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "rag_seeds"
    _VICTORIES = _FIXTURES / "victories.json"
    _SEEDS_FALLBACK = _FIXTURES / "seeds.json"
    _INDUSTRY_CASES = _FIXTURES / "industry_cases.json"

    def __init__(self, collection_name: str = "tenex_delivered") -> None:
        self._collection_name = collection_name

    def add(self, docs: list[dict[str, Any]]) -> None:
        return None

    def query(self, text: str, k: int = 3) -> list[dict[str, Any]]:
        try:
            if self._collection_name == "industry_cases":
                source = self._INDUSTRY_CASES
                if not source.exists():
                    return [{"id": "ind-000", "embed_text": "Mock industry case", "industry": "general"}]
            else:
                source = self._VICTORIES if self._VICTORIES.exists() else self._SEEDS_FALLBACK
            records = json.loads(source.read_text())
            detected = _detect_industry(text)
            if detected:
                return _filter_by_industry(records, detected, k)
            return records[:k]
        except FileNotFoundError:
            return [{"id": "win-000", "embed_text": "Mock seed: AI transformation solution", "industry": "general"}]


def get_vector_store(collection_name: str = "tenex_delivered") -> VectorStore:
    """Factory — returns the correct store based on env vars."""
    if os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes"):
        return MockStore(collection_name=collection_name)

    store_type = os.getenv("VECTOR_STORE", "chroma").lower()
    if store_type == "chroma":
        return ChromaStore(collection_name=collection_name)

    return MockStore(collection_name=collection_name)
