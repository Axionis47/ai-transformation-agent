from __future__ import annotations

from core.schemas import EvidenceItem


class EvidenceAccumulator:
    """Accumulates EvidenceItems across reasoning loops. Deduplicates by source_ref."""

    def __init__(self, initial: list[EvidenceItem] | None = None) -> None:
        self._items: dict[str, EvidenceItem] = {}
        if initial:
            for item in initial:
                self.add(item)

    def add(self, item: EvidenceItem) -> bool:
        """Add single item. Returns True if new, False if duplicate (lower score kept)."""
        existing = self._items.get(item.source_ref)
        if existing is not None:
            if item.relevance_score > existing.relevance_score:
                self._items[item.source_ref] = item
            return False
        self._items[item.source_ref] = item
        return True

    def add_many(self, items: list[EvidenceItem]) -> int:
        """Add multiple items. Returns count of newly added (not duplicates)."""
        return sum(1 for item in items if self.add(item))

    def get_all(self) -> list[EvidenceItem]:
        """Return all items sorted by relevance_score descending."""
        return sorted(self._items.values(), key=lambda e: e.relevance_score, reverse=True)

    def get_ids(self) -> list[str]:
        """Return evidence_id for all stored items."""
        return [item.evidence_id for item in self._items.values()]

    def count(self) -> int:
        return len(self._items)

    def source_types(self) -> set[str]:
        """Return unique source_type values as strings."""
        return {item.source_type.value for item in self._items.values()}
