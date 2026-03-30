"""In-memory storage backend — wraps the existing _runs dict pattern.

Used for local dev and tests. Implements StorageProtocol.
"""

from __future__ import annotations

from core.schemas import Run


class MemoryStore:
    """In-memory run storage. Fast but lost on restart."""

    def __init__(self) -> None:
        self._runs: dict[str, Run] = {}

    def save_run(self, run: Run) -> None:
        self._runs[run.run_id] = run

    def get_run(self, run_id: str) -> Run | None:
        return self._runs.get(run_id)

    def list_runs(self, limit: int = 50, offset: int = 0) -> list[Run]:
        runs = sorted(
            self._runs.values(),
            key=lambda r: r.created_at,
            reverse=True,
        )
        return runs[offset : offset + limit]

    def delete_run(self, run_id: str) -> bool:
        if run_id in self._runs:
            del self._runs[run_id]
            return True
        return False
