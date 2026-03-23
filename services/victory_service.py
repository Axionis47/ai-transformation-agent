"""Victory service — decoupled RAG wrapper for session-based queries."""
from __future__ import annotations

from agents.base import AgentError
from rag.vector_store import get_vector_store


class VictoryService:
    """Thin query interface over the victory and industry case libraries."""

    def __init__(self, dry_run: bool = False) -> None:
        self._delivered_store = get_vector_store(
            collection_name="tenex_delivered", dry_run=dry_run,
        )
        self._industry_store = get_vector_store(
            collection_name="industry_cases", dry_run=dry_run,
        )

    def query_victories(self, text: str, k: int = 5) -> list[dict]:
        """Search delivered victories by semantic similarity."""
        result = self._delivered_store.query(text, k=k)
        if isinstance(result, AgentError):
            return []
        return result

    def query_industry_cases(self, text: str, k: int = 3) -> list[dict]:
        """Search industry case studies by semantic similarity."""
        result = self._industry_store.query(text, k=k)
        if isinstance(result, AgentError):
            return []
        return result

    def get_all_victories(self) -> list[dict]:
        """Return all delivered victories for broad matching."""
        result = self._delivered_store.query_all()
        if isinstance(result, AgentError):
            return []
        return result
