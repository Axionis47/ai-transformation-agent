"""Opportunity store: typed storage separate from Run object."""

from __future__ import annotations

from core.schemas import Opportunity


class OpportunityStore:
    """Per-run opportunity storage."""

    def __init__(self) -> None:
        self._items: dict[str, list[Opportunity]] = {}

    def store(self, run_id: str, opportunities: list[Opportunity]) -> None:
        """Store opportunities for a run (replaces any existing)."""
        self._items[run_id] = list(opportunities)

    def get_all(self, run_id: str) -> list[Opportunity]:
        """Return all opportunities for a run."""
        return list(self._items.get(run_id, []))

    def count(self, run_id: str) -> int:
        return len(self._items.get(run_id, []))


# Module-level singleton
_store = OpportunityStore()


def get_opportunity_store() -> OpportunityStore:
    return _store
