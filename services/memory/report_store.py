"""Report store: typed storage separate from Run object."""
from __future__ import annotations


class ReportStore:
    """Per-run report storage."""

    def __init__(self) -> None:
        self._items: dict[str, dict] = {}

    def store(self, run_id: str, report: dict) -> None:
        """Store report for a run."""
        self._items[run_id] = report

    def get(self, run_id: str) -> dict:
        """Return report for a run, empty dict if none."""
        return self._items.get(run_id, {})


# Module-level singleton
_store = ReportStore()


def get_report_store() -> ReportStore:
    return _store
