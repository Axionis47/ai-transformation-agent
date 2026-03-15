"""Structured JSONL logger — all pipeline logging goes through here."""

from __future__ import annotations

import json
import time
from pathlib import Path

_LOG_DIR = Path("logs/runs")


class PipelineLogger:
    """Appends structured JSONL entries to a per-run log file."""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        self._path = _LOG_DIR / f"{run_id}.jsonl"

    def log(self, agent_tag: str, event: str, **kwargs: object) -> None:
        """Write one log entry. Extra kwargs are merged into the entry."""
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "run_id": self.run_id,
            "agent_tag": agent_tag,
            "event": event,
            **kwargs,
        }
        with open(self._path, "a") as fh:
            fh.write(json.dumps(entry) + "\n")

    @property
    def log_path(self) -> Path:
        return self._path


def get_logger(run_id: str) -> PipelineLogger:
    """Factory — returns a logger scoped to the given run_id."""
    return PipelineLogger(run_id)
