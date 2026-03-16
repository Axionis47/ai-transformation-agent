"""Tests for pipeline hardening: timeouts, logger, and cost tracking."""

from __future__ import annotations

import json
import time
from pathlib import Path

from agents.base import AgentError, BaseAgent
from ops.logger import get_logger
from orchestrator.pipeline import _run_with_timeout, run_pipeline
from orchestrator.state import PipelineState, PipelineStatus


class _SlowAgent(BaseAgent):
    """Stub agent that sleeps longer than the timeout."""

    agent_tag = "SLOW"

    def _run(self, input_data: dict) -> object:
        time.sleep(10)
        return {}


def test_timeout_produces_agent_error():
    """An agent exceeding the timeout should return AgentError(code='TIMEOUT')."""
    result = _run_with_timeout(_SlowAgent(), {"url": "https://example.com"}, timeout=1)

    assert isinstance(result, AgentError), f"Expected AgentError, got {type(result)}"
    assert result.code == "TIMEOUT"
    assert result.agent_tag == "SLOW"
    assert result.recoverable is False


def test_jsonl_output(monkeypatch, tmp_path, capsys):
    """Dry-run pipeline should write a valid JSONL log file."""
    import ops.logger as logger_module

    # Redirect log output to a temp directory
    monkeypatch.setattr(logger_module, "_LOG_DIR", tmp_path)

    monkeypatch.setenv("DRY_RUN", "true")
    state = run_pipeline(url="https://example.com", dry_run=True)

    assert state.status == PipelineStatus.COMPLETE

    log_files = list(tmp_path.glob("*.jsonl"))
    assert len(log_files) == 1, "Expected exactly one JSONL log file"

    lines = log_files[0].read_text().strip().splitlines()
    assert len(lines) >= 5, f"Expected at least 5 log entries, got {len(lines)}"

    for line in lines:
        entry = json.loads(line)
        assert "timestamp" in entry
        assert "run_id" in entry
        assert "agent_tag" in entry
        assert "event" in entry


def test_cost_accumulation_dry_run(monkeypatch):
    """Dry-run pipeline must not accumulate cost (cost_usd stays 0.0)."""
    monkeypatch.setenv("DRY_RUN", "true")
    state = run_pipeline(url="https://example.com", dry_run=True)

    assert state.status == PipelineStatus.COMPLETE
    assert state.cost_usd == 0.0, (
        f"Dry-run should not accumulate cost, got {state.cost_usd}"
    )
