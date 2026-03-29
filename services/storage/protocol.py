"""Storage protocol — interface for run persistence.

Both MemoryStore and FirestoreStore implement this.
run_manager calls these methods; never talks to a backend directly.
"""
from __future__ import annotations

from typing import Protocol

from core.schemas import Run


class StorageProtocol(Protocol):
    """Interface every storage backend must implement."""

    def save_run(self, run: Run) -> None:
        """Persist full run state. Called after every mutation."""
        ...

    def get_run(self, run_id: str) -> Run | None:
        """Load a run by ID. Returns None if not found."""
        ...

    def list_runs(self, limit: int = 50, offset: int = 0) -> list[Run]:
        """List runs ordered by created_at descending."""
        ...

    def delete_run(self, run_id: str) -> bool:
        """Delete a run. Returns True if found and deleted."""
        ...
