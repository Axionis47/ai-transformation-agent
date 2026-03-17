"""Tests for ops/logger.py — log_agent_call and truncation helpers."""

from __future__ import annotations

import json
import time
from pathlib import Path


from ops.logger import PipelineLogger, _truncate, _truncate_summary


# ---------------------------------------------------------------------------
# Truncation helpers
# ---------------------------------------------------------------------------

def test_truncate_short_string_unchanged():
    assert _truncate("hello") == "hello"


def test_truncate_long_string_gets_ellipsis():
    long = "x" * 250
    result = _truncate(long)
    assert result.endswith("...")
    assert len(result) == 203  # 200 chars + "..."


def test_truncate_short_list_unchanged():
    items = [1, 2, 3]
    assert _truncate(items) == [1, 2, 3]


def test_truncate_long_list_gets_marker():
    items = [1, 2, 3, 4, 5]
    result = _truncate(items)
    assert len(result) == 4
    assert result[-1] == "[+2 more]"


def test_truncate_summary_applies_to_all_values():
    summary = {"text": "a" * 250, "items": [1, 2, 3, 4]}
    result = _truncate_summary(summary)
    assert result["text"].endswith("...")
    assert result["items"][-1] == "[+1 more]"


def test_truncate_summary_none_returns_none():
    assert _truncate_summary(None) is None


# ---------------------------------------------------------------------------
# Backward compatibility — existing log() calls still work
# ---------------------------------------------------------------------------

def test_log_backward_compatible(tmp_path, monkeypatch):
    monkeypatch.setattr("ops.logger._LOG_DIR", tmp_path)
    logger = PipelineLogger("test-run-compat")
    logger._path = tmp_path / "test-run-compat.jsonl"
    logger.log("SCRAPER", "complete", elapsed_ms=123)
    lines = logger._path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["event"] == "complete"
    assert entry["elapsed_ms"] == 123
    assert "input_summary" not in entry
    assert "output_summary" not in entry


# ---------------------------------------------------------------------------
# log_agent_call — start event
# ---------------------------------------------------------------------------

def test_log_agent_call_start_writes_agent_start(tmp_path, monkeypatch):
    monkeypatch.setattr("ops.logger._LOG_DIR", tmp_path)
    logger = PipelineLogger("test-run-start")
    logger._path = tmp_path / "test-run-start.jsonl"
    logger.log_agent_call(
        "SCRAPER",
        prompt_file="prompts/scraper.md",
        prompt_version="1.0",
        input_summary={"url": "https://example.com"},
    )
    lines = logger._path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["event"] == "agent_start"
    assert entry["agent_tag"] == "SCRAPER"
    assert entry["input_summary"]["url"] == "https://example.com"
    assert entry["prompt_file"] == "prompts/scraper.md"


# ---------------------------------------------------------------------------
# log_agent_call — complete event with latency
# ---------------------------------------------------------------------------

def test_log_agent_call_complete_has_latency(tmp_path, monkeypatch):
    monkeypatch.setattr("ops.logger._LOG_DIR", tmp_path)
    logger = PipelineLogger("test-run-complete")
    logger._path = tmp_path / "test-run-complete.jsonl"
    t_start = time.time() - 0.5  # 500ms ago
    logger.log_agent_call(
        "REPORT_WRITER",
        result={"sections": 5},
        start_time=t_start,
        prompt_file="prompts/report_writer.md",
        prompt_version="1.0",
        output_summary={"sections_present": ["exec_summary"], "total_chars": 2000},
    )
    lines = logger._path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["event"] == "agent_complete"
    assert entry["latency_ms"] > 0
    assert entry["output_summary"]["total_chars"] == 2000


# ---------------------------------------------------------------------------
# Dry-run pipeline produces per-stage I/O entries
# ---------------------------------------------------------------------------

def test_dry_run_produces_io_log_entries(monkeypatch):
    from orchestrator.pipeline import run_pipeline
    from orchestrator.state import PipelineStatus

    monkeypatch.setenv("DRY_RUN", "true")
    state = run_pipeline(url="https://example.com", dry_run=True)
    assert state.status == PipelineStatus.COMPLETE

    log_path = Path("logs/runs") / f"{state.run_id}.jsonl"
    assert log_path.exists(), f"Log file not found: {log_path}"

    entries = [json.loads(line) for line in log_path.read_text().strip().splitlines()]
    events = [e["event"] for e in entries]

    assert "agent_start" in events, "Expected at least one agent_start event"
    assert "agent_complete" in events, "Expected at least one agent_complete event"

    # Verify SCRAPER start entry has input_summary with url
    scraper_starts = [e for e in entries if e.get("agent_tag") == "SCRAPER" and e.get("event") == "agent_start"]
    assert scraper_starts, "No SCRAPER agent_start entry found"
    assert "input_summary" in scraper_starts[0]

    # Verify REPORT_WRITER complete entry has output_summary
    rw_completes = [e for e in entries if e.get("agent_tag") == "REPORT_WRITER" and e.get("event") == "agent_complete"]
    assert rw_completes, "No REPORT_WRITER agent_complete entry found"
    assert "output_summary" in rw_completes[0]
