from __future__ import annotations

import uuid

from pydantic import BaseModel

from core.events import EventType
from core.schemas import BudgetState, EvidenceItem, EvidenceSource, Provenance
from services.rag.store import RAGStore
from services.trace import emit


class RAGQueryResult(BaseModel):
    results: list[EvidenceItem]
    query: str
    budget_exhausted: bool = False
    filtered_count: int = 0  # count of results removed by min_score filter


class RAGRetriever:
    """Semantic search over Wins KB with budget enforcement and trace emission."""

    def __init__(self, store: RAGStore, config: dict) -> None:
        budgets = config.get("budgets", config)
        self._store = store
        self._top_k: int = int(budgets.get("rag_top_k", 5))
        self._min_score: float = float(budgets.get("rag_min_score", 0.3))
        self._query_budget: int = int(budgets.get("rag_query_budget", 8))

    def query(
        self,
        query_text: str,
        run_id: str,
        budget_state: BudgetState,
    ) -> RAGQueryResult:
        # 1. Budget check
        if budget_state.rag_queries_used >= self._query_budget:
            emit(
                run_id,
                EventType.BUDGET_VIOLATION_BLOCKED,
                {
                    "resource": "rag_queries",
                    "used": budget_state.rag_queries_used,
                    "budget": self._query_budget,
                },
            )
            return RAGQueryResult(results=[], query=query_text, budget_exhausted=True)

        # 2. Raw semantic search
        raw = self._store.query(query_text, top_k=self._top_k)

        # 3. Score filter
        before_count = len(raw)
        filtered = [r for r in raw if r["score"] >= self._min_score]
        filtered_count = before_count - len(filtered)
        emit(
            run_id,
            EventType.RAG_RESULTS_FILTERED,
            {
                "query": query_text,
                "before": before_count,
                "after": len(filtered),
                "filtered_out": filtered_count,
                "min_score": self._min_score,
            },
        )

        # 4. Normalise into EvidenceItems
        evidence_items: list[EvidenceItem] = []
        for i, r in enumerate(filtered):
            evidence_items.append(
                EvidenceItem(
                    evidence_id=str(uuid.uuid4()),
                    run_id=run_id,
                    source_type=EvidenceSource.WINS_KB,
                    source_ref=r["metadata"].get("engagement_id", r["id"]),
                    title=r["metadata"].get("title", r["id"]),
                    snippet=r["text"][:500],
                    relevance_score=round(r["score"], 4),
                    retrieval_meta={"query": query_text, "rank": i},
                    provenance=Provenance(
                        source_type="raw",
                        source_evidence_ids=[],
                        confidence=round(r["score"], 4),
                    ),
                )
            )

        # 5. Increment budget
        budget_state.rag_queries_used += 1

        # 6. Emit execution trace
        emit(
            run_id,
            EventType.RAG_QUERY_EXECUTED,
            {
                "query": query_text,
                "results_returned": len(evidence_items),
                "rag_queries_used": budget_state.rag_queries_used,
            },
        )

        return RAGQueryResult(
            results=evidence_items,
            query=query_text,
            budget_exhausted=False,
            filtered_count=filtered_count,
        )
