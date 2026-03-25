"""Contradiction detection: identifies conflicting evidence from different sources."""
from __future__ import annotations

from dataclasses import dataclass

from core.schemas import EvidenceItem, EvidenceSource

# Fields where user corrections can conflict with grounding data
SCALE_FIELDS = {"employee_count", "revenue", "headcount", "company_size", "employees"}


@dataclass
class Contradiction:
    """A detected conflict between evidence items."""
    field: str
    existing_evidence_id: str
    new_evidence_id: str
    resolution: str  # "new_wins" | "existing_wins" | "flagged"


class ContradictionDetector:
    """Detects conflicts between evidence items from different sources.

    Scope: USER_PROVIDED vs non-USER_PROVIDED on scale-related fields.
    Resolution: USER_PROVIDED always wins (user is the authority on their company).
    """

    def check(
        self, existing: list[EvidenceItem], new_item: EvidenceItem
    ) -> list[Contradiction]:
        """Check if new_item contradicts any existing evidence.

        Only checks cross-source contradictions (same source type = no conflict).
        """
        contradictions: list[Contradiction] = []
        for ex in existing:
            if ex.source_type == new_item.source_type:
                continue
            field = self._find_shared_field(ex, new_item)
            if field is None:
                continue
            if new_item.source_type == EvidenceSource.USER_PROVIDED:
                resolution = "new_wins"
            elif ex.source_type == EvidenceSource.USER_PROVIDED:
                resolution = "existing_wins"
            else:
                resolution = "flagged"
            contradictions.append(Contradiction(
                field=field,
                existing_evidence_id=ex.evidence_id,
                new_evidence_id=new_item.evidence_id,
                resolution=resolution,
            ))
        return contradictions

    def _find_shared_field(self, a: EvidenceItem, b: EvidenceItem) -> str | None:
        """Check if two items cover the same scale field."""
        overlap = self._extract_fields(a) & self._extract_fields(b)
        return next(iter(overlap), None)

    @staticmethod
    def _extract_fields(item: EvidenceItem) -> set[str]:
        """Extract scale-field keywords from an evidence item's text."""
        fields: set[str] = set()
        text = f"{item.title} {item.snippet}".lower()
        for kw in SCALE_FIELDS:
            if kw in text:
                fields.add(kw)
        meta_field = item.retrieval_meta.get("field", "")
        if meta_field:
            fields.add(meta_field.lower())
        return fields
