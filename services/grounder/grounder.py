from __future__ import annotations

import uuid

from pydantic import BaseModel

from core.events import EventType
from core.schemas import BudgetState, EvidenceItem, EvidenceSource, Provenance
from services.grounder.parser import ParsedGroundingMetadata, parse_grounding_response
from services.trace import emit


class GroundingResult(BaseModel):
    text: str
    evidence_items: list[EvidenceItem]
    search_queries_used: int
    budget_exhausted: bool = False
    coverage_gap: str | None = None


class Grounder:
    def __init__(self, client: object, config: dict) -> None:
        budgets = config.get("budgets", config)
        self._client = client
        self._query_budget: int = int(budgets.get("external_search_query_budget", 5))
        self._max_calls: int = int(budgets.get("external_search_max_calls", 3))

    def reason(self, prompt: str, run_id: str) -> str:
        """Pure reasoning call — no Google Search, no budget cost.

        Used for ReAct thinking steps, assumption extraction, and opportunity evaluation.
        Falls back gracefully if the model call fails (e.g., no credentials).
        """
        try:
            raw = self._client.generate(prompt)  # type: ignore[attr-defined]
            return raw.get("text", "")
        except Exception:
            return ""

    def ground(self, prompt: str, run_id: str, budget_state: BudgetState) -> GroundingResult:
        # Layer 1: query budget check
        if budget_state.external_search_queries_used >= self._query_budget:
            emit(run_id, EventType.EXTERNAL_BUDGET_EXHAUSTED, {
                "reason": "search query budget exhausted",
                "used": budget_state.external_search_queries_used,
                "budget": self._query_budget,
            })
            return GroundingResult(
                text="", evidence_items=[], search_queries_used=0,
                budget_exhausted=True, coverage_gap="search query budget exhausted",
            )

        # Layer 2: call count check (defense-in-depth)
        if budget_state.external_search_calls_used >= self._max_calls:
            emit(run_id, EventType.BUDGET_VIOLATION_BLOCKED, {
                "resource": "external_search_calls",
                "used": budget_state.external_search_calls_used,
                "budget": self._max_calls,
            })
            return GroundingResult(
                text="", evidence_items=[], search_queries_used=0,
                budget_exhausted=True, coverage_gap="api call limit reached",
            )

        emit(run_id, EventType.GROUNDING_CALL_REQUESTED, {
            "prompt": prompt[:200],
            "run_id": run_id,
            "calls_used": budget_state.external_search_calls_used,
            "queries_used": budget_state.external_search_queries_used,
        })

        raw = self._client.generate_with_grounding(prompt)  # type: ignore[attr-defined]
        budget_state.external_search_calls_used += 1

        parsed: ParsedGroundingMetadata = parse_grounding_response(raw)
        budget_state.external_search_queries_used += parsed.search_query_count

        emit(run_id, EventType.GROUNDING_QUERIES_COUNTED, {
            "queries": parsed.search_queries,
            "count": parsed.search_query_count,
            "total_used": budget_state.external_search_queries_used,
            "budget": self._query_budget,
        })

        if budget_state.external_search_queries_used >= self._query_budget:
            emit(run_id, EventType.EXTERNAL_BUDGET_EXHAUSTED, {
                "reason": "query budget reached after call",
                "used": budget_state.external_search_queries_used,
                "budget": self._query_budget,
            })

        evidence_items = self._normalize_evidence(parsed, run_id, prompt)

        emit(run_id, EventType.GROUNDING_CALL_COMPLETED, {
            "text_length": len(parsed.text),
            "chunks_count": len(parsed.chunks),
            "supports_count": len(parsed.supports),
        })

        return GroundingResult(
            text=parsed.text,
            evidence_items=evidence_items,
            search_queries_used=parsed.search_query_count,
        )

    @staticmethod
    def _sanitize(text: str) -> str:
        """Remove control characters that break JSON serialization."""
        return "".join(c if c >= " " or c in "\n\t" else " " for c in text)

    def _normalize_evidence(
        self, parsed: ParsedGroundingMetadata, run_id: str, prompt: str
    ) -> list[EvidenceItem]:
        items: list[EvidenceItem] = []
        for idx, chunk in enumerate(parsed.chunks):
            matching = [s for s in parsed.supports if idx in s.chunk_indices]
            if matching:
                snippet_parts = [s.segment_text for s in matching]
                all_scores = [c for s in matching for c in s.confidence_scores]
                relevance = round(sum(all_scores) / len(all_scores), 4) if all_scores else 0.5
                confidence = round(max(all_scores), 4) if all_scores else 0.5
                snippet = self._sanitize(" ".join(snippet_parts)[:500])
            else:
                snippet = self._sanitize(parsed.text[:500])
                relevance = 0.5
                confidence = 0.5

            items.append(EvidenceItem(
                evidence_id=str(uuid.uuid4()),
                run_id=run_id,
                source_type=EvidenceSource.GOOGLE_SEARCH,
                source_ref=chunk.uri,
                title=self._sanitize(chunk.title),
                uri=chunk.uri,
                snippet=snippet,
                relevance_score=relevance,
                confidence_score=confidence,
                retrieval_meta={
                    "query": prompt,
                    "domain": chunk.domain,
                    "search_queries": parsed.search_queries,
                },
                provenance=Provenance(
                    source_type="raw",
                    source_evidence_ids=[],
                    confidence=confidence,
                ),
            ))
        return items
