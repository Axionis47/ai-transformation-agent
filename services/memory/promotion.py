"""Promotion gate: observe-validate-promote pipeline for evidence."""
from __future__ import annotations

from dataclasses import dataclass, field

from core.events import EventType
from core.schemas import EvidenceItem
from services.memory.contradiction import ContradictionDetector
from services.memory.store import EvidenceStore
from services.trace import emit


@dataclass
class PromotionResult:
    """Outcome of a batch promotion attempt."""

    accepted: int = 0
    rejected: int = 0
    accepted_items: list[EvidenceItem] = field(default_factory=list)
    rejection_reasons: list[str] = field(default_factory=list)


PHASE_THRESHOLDS = {
    "grounding": 0.3,
    "deep_research": 0.4,
    "hypothesis_testing": 0.5,
}


class PromotionGate:
    """Validates evidence candidates before writing to EvidenceStore.

    Pipeline:
    1. Schema check: evidence_id and source_type must be present
    2. Relevance threshold (phase-aware, scales with pipeline depth)
    3. Dedup via store.add() which handles score-based replacement
    4. Emit EVIDENCE_PROMOTED / EVIDENCE_REJECTED trace events
    """

    def __init__(self, store: EvidenceStore, min_relevance: float = 0.3) -> None:
        self._store = store
        self._min_relevance = min_relevance

    def promote_batch(
        self,
        run_id: str,
        candidates: list[EvidenceItem],
        source_label: str = "unknown",
        phase: str = "grounding",
    ) -> PromotionResult:
        """Validate and promote a batch of evidence candidates."""
        result = PromotionResult()
        detector = ContradictionDetector()
        threshold = PHASE_THRESHOLDS.get(phase, self._min_relevance)

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

            # Step 2: Phase-aware relevance threshold
            if item.relevance_score < threshold:
                reason = (
                    f"relevance {item.relevance_score:.3f} below threshold "
                    f"{threshold:.3f} for {item.evidence_id}"
                )
                result.rejected += 1
                result.rejection_reasons.append(reason)
                emit(run_id, EventType.EVIDENCE_REJECTED, {
                    "evidence_id": item.evidence_id,
                    "relevance_score": item.relevance_score,
                    "threshold": threshold,
                    "reason": reason,
                    "source_label": source_label,
                })
                continue

            # Step 2.5: Contradiction detection
            existing = self._store.get_all(run_id)
            contradictions = detector.check(existing, item)
            for c in contradictions:
                emit(run_id, EventType.EVIDENCE_CONTRADICTION, {
                    "field": c.field,
                    "existing_id": c.existing_evidence_id,
                    "new_id": c.new_evidence_id,
                    "resolution": c.resolution,
                    "source_label": source_label,
                })

            # Step 3: Dedup via store (handles score-based replacement)
            is_new = self._store.add(run_id, item)
            result.accepted += 1
            result.accepted_items.append(item)

            emit(run_id, EventType.EVIDENCE_PROMOTED, {
                "evidence_id": item.evidence_id,
                "source_type": item.source_type.value,
                "relevance_score": item.relevance_score,
                "is_new": is_new,
                "source_label": source_label,
            })

        return result
