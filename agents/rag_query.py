"""RAG query agent — retrieves similar AI solutions from vector store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.base import AgentError, BaseAgent
from rag.vector_store import get_vector_store

_SEEDS = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "rag_seeds" / "seeds.json"


class RAGQueryAgent(BaseAgent):
    """Queries vector store for similar AI transformation solutions."""

    agent_tag = "RAG"

    def _run(self, state: Any) -> list[dict] | AgentError:
        if self.dry_run:
            try:
                seeds = json.loads(_SEEDS.read_text())
                return seeds[:3]
            except FileNotFoundError:
                return [{"text": "Mock: AI solution", "industry": "general"}]

        company_data = state.company_data if hasattr(state, "company_data") else state
        query_text = self._build_query(company_data)
        store = get_vector_store()
        return store.query(query_text, k=3)

    def _build_query(self, company_data: dict) -> str:
        parts = []
        if company_data.get("about_text"):
            parts.append(company_data["about_text"][:500])
        if company_data.get("job_postings"):
            parts.append(" ".join(company_data["job_postings"][:3]))
        return " ".join(parts) if parts else "AI transformation solutions"
