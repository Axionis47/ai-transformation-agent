"""Structured JSONL logger — all pipeline logging goes through here."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_LOG_DIR = Path("logs/runs")
_MAX_STR_LEN = 200
_MAX_LIST_ITEMS = 3


def _truncate(value: Any) -> Any:
    """Truncate strings > 200 chars and lists > 3 items for log safety."""
    if isinstance(value, str) and len(value) > _MAX_STR_LEN:
        return value[:_MAX_STR_LEN] + "..."
    if isinstance(value, list) and len(value) > _MAX_LIST_ITEMS:
        extra = len(value) - _MAX_LIST_ITEMS
        return value[:_MAX_LIST_ITEMS] + [f"[+{extra} more]"]
    return value


def _truncate_summary(summary: dict[str, Any] | None) -> dict[str, Any] | None:
    """Apply truncation to every value in a summary dict."""
    if summary is None:
        return None
    return {k: _truncate(v) for k, v in summary.items()}


class PipelineLogger:
    """Appends structured JSONL entries to a per-run log file."""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        self._path = _LOG_DIR / f"{run_id}.jsonl"

    def log(
        self,
        agent_tag: str,
        event: str,
        *,
        input_summary: dict[str, Any] | None = None,
        output_summary: dict[str, Any] | None = None,
        **kwargs: object,
    ) -> None:
        """Write one log entry. Extra kwargs are merged into the entry."""
        entry: dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "run_id": self.run_id,
            "agent_tag": agent_tag,
            "event": event,
            **kwargs,
        }
        if input_summary is not None:
            entry["input_summary"] = _truncate_summary(input_summary)
        if output_summary is not None:
            entry["output_summary"] = _truncate_summary(output_summary)
        with open(self._path, "a") as fh:
            fh.write(json.dumps(entry) + "\n")

    def log_agent_call(
        self,
        agent_tag: str,
        *,
        result: Any = None,
        start_time: float | None = None,
        prompt_file: str | None = None,
        prompt_version: str | None = None,
        input_summary: dict[str, Any] | None = None,
        output_summary: dict[str, Any] | None = None,
    ) -> None:
        """Log agent_start or agent_complete depending on whether result is provided."""
        if result is None and output_summary is None:
            # Starting the agent
            self.log(
                agent_tag,
                "agent_start",
                prompt_file=prompt_file,
                prompt_version=prompt_version,
                input_summary=input_summary,
            )
        else:
            # Agent completed
            latency_ms = (
                int((time.time() - start_time) * 1000) if start_time is not None else None
            )
            self.log(
                agent_tag,
                "agent_complete",
                prompt_file=prompt_file,
                prompt_version=prompt_version,
                latency_ms=latency_ms,
                output_summary=output_summary,
            )

    def flush_to_gcs(self, run_id: str) -> None:
        """Upload the local JSONL trace to GCS if GCS_TRACE_BUCKET is set.

        Safe to call when GCS is not configured — does nothing in that case.
        Local file is preserved after upload (kept for dry-run and local dev).
        """
        import os

        bucket_name = os.getenv("GCS_TRACE_BUCKET", "")
        if not bucket_name or not self._path.exists():
            return
        try:
            from google.cloud import storage  # noqa: PLC0415

            client = storage.Client()
            blob = client.bucket(bucket_name).blob(f"traces/{run_id}.jsonl")
            blob.upload_from_filename(str(self._path))
        except Exception:
            pass  # GCS unavailable — local file remains the source of truth

    @property
    def log_path(self) -> Path:
        return self._path


def get_logger(run_id: str) -> PipelineLogger:
    """Factory — returns a logger scoped to the given run_id."""
    return PipelineLogger(run_id)
