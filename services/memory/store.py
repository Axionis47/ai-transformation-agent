"""Evidence store: typed storage separate from Run object.

Wraps evidence by run_id. Supports add, get, filter, and prune operations.
Run object will hold evidence_ids references; this store holds the actual items.
"""
from __future__ import annotations

from core.schemas import EvidenceItem


class EvidenceStore:
    """Per-run evidence storage with filtering and pruning support."""

    def __init__(self) -> None:
        self._items: dict[str, dict[str, EvidenceItem]] = {}  # run_id -> {evidence_id -> item}

    def add(self, run_id: str, item: EvidenceItem) -> bool:
        """Add item. Returns True if new, False if duplicate (keeps higher score)."""
        store = self._items.setdefault(run_id, {})
        existing = store.get(item.evidence_id)
        if existing is not None:
            if item.relevance_score > existing.relevance_score:
                store[item.evidence_id] = item
            return False
        store[item.evidence_id] = item
        return True

    def add_many(self, run_id: str, items: list[EvidenceItem]) -> int:
        """Add multiple items. Returns count of newly added."""
        return sum(1 for item in items if self.add(run_id, item))

    def get_all(self, run_id: str) -> list[EvidenceItem]:
        """Return all items sorted by relevance descending."""
        store = self._items.get(run_id, {})
        return sorted(store.values(), key=lambda e: e.relevance_score, reverse=True)

    def get_by_ids(self, run_id: str, ids: list[str]) -> list[EvidenceItem]:
        """Return specific items by evidence_id."""
        store = self._items.get(run_id, {})
        return [store[eid] for eid in ids if eid in store]

    def get_filtered(
        self,
        run_id: str,
        min_relevance: float = 0.0,
        max_items: int = 50,
        source_types: list[str] | None = None,
    ) -> tuple[list[EvidenceItem], int]:
        """Return filtered items and count of dropped items."""
        all_items = self.get_all(run_id)
        total = len(all_items)
        filtered = all_items

        if min_relevance > 0:
            filtered = [e for e in filtered if e.relevance_score >= min_relevance]

        if source_types is not None:
            type_set = set(source_types)
            filtered = [e for e in filtered if e.source_type.value in type_set]

        filtered = filtered[:max_items]
        dropped = total - len(filtered)
        return filtered, dropped

    def count(self, run_id: str) -> int:
        return len(self._items.get(run_id, {}))

    def get_ids(self, run_id: str) -> list[str]:
        return list(self._items.get(run_id, {}).keys())

    def prune(self, run_id: str, min_relevance: float, max_items: int) -> int:
        """Remove low-relevance items. Returns count of pruned items."""
        store = self._items.get(run_id, {})
        if not store:
            return 0
        before = len(store)
        # Remove below threshold
        to_remove = [eid for eid, e in store.items() if e.relevance_score < min_relevance]
        for eid in to_remove:
            del store[eid]
        # If still over max, remove lowest scoring
        if len(store) > max_items:
            sorted_items = sorted(store.values(), key=lambda e: e.relevance_score)
            excess = len(store) - max_items
            for item in sorted_items[:excess]:
                del store[item.evidence_id]
        return before - len(store)


# Module-level singleton
_store = EvidenceStore()


def get_evidence_store() -> EvidenceStore:
    return _store
