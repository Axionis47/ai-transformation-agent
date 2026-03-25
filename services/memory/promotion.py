"""Promotion gate: observe-validate-promote pipeline for evidence."""
from __future__ import annotations

from dataclasses import dataclass, field

from core.events import EventType
from core.schemas import EvidenceItem
from services.memory.store import EvidenceStore
from services.trace import emit


@dataclass
class PromotionResult:
    """Outcome of a batch promotion attempt."""

    accepted: int = 0
    rejected: int = 0
    rejection_reasons: list[str] = field(default_factory=list)


class PromotionGate:
    """Validates evidence candidates before writing to EvidenceStore.

    Pipeline:
    1. Schema check: evidence_id and source_type must be present
    2. Relevance threshold (configurable, default 0.0 = accept all)
    3. Dedup via store.add() which handles score-based replacement
    4. Emit EVIDENCE_PROMOTED / EVIDENCE_REJECTED trace events
    """

    def __init__(self, store: EvidenceStore, min_relevance: float = 0.0) -> None:
        self._store = store
        self._min_relevance = min_relevance

    def promote_batch(
        self,
        run_id: str,
        candidates: list[EvidenceItem],
        source_label: str = "unknown",
    ) -> PromotionResult:
        """Validate and promote a batch of evidence candidates."""
        result = PromotionResult()

        for item in candidates:
            # Step 1: Schema check
            if not item.evidence_id or not item.source_type:
                reason = "missing required field (evidence_id or source_type) on item"
                result.rejected += 1
                result.rejection_reasons.append(reason)
                emit(run_id, EventType.EVIDENCE_REJECTED, {
                    "reason": reason,
                    "source_label": source_label,
                })
                continue

            # Step 2: Relevance threshold
            if item.relevance_score < self._min_relevance:
                reason = (
                    f"relevance {item.relevance_score:.3f} below threshold "
                    f"{self._min_relevance:.3f} for {item.evidence_id}"
                )
                result.rejected += 1
                result.rejection_reasons.append(reason)
                emit(run_id, EventType.EVIDENCE_REJECTED, {
                    "evidence_id": item.evidence_id,
                    "relevance_score": item.relevance_score,
                    "threshold": self._min_relevance,
                    "reason": reason,
                    "source_label": source_label,
                })
                continue

            # Step 3: Dedup via store (handles score-based replacement)
            is_new = self._store.add(run_id, item)
            result.accepted += 1

            emit(run_id, EventType.EVIDENCE_PROMOTED, {
                "evidence_id": item.evidence_id,
                "source_type": item.source_type.value,
                "relevance_score": item.relevance_score,
                "is_new": is_new,
                "source_label": source_label,
            })

        return result
