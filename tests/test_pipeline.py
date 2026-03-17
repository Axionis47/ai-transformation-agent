"""Tests for orchestrator/pipeline.py — dry-run end-to-end."""

from unittest.mock import MagicMock, patch

from orchestrator.pipeline import _parallel_report_sections, run_pipeline
from orchestrator.state import PipelineStatus


def test_dry_run_completes(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    state = run_pipeline(url="https://example.com", dry_run=True)

    assert state.status == PipelineStatus.COMPLETE
    assert state.company_data is not None
    assert state.rag_context is not None
    assert state.analysis is not None
    assert state.report is not None

    # All 5 report sections present and non-empty
    for section in ["exec_summary", "current_state", "use_cases", "roadmap", "roi_analysis"]:
        assert section in state.report, f"Missing section: {section}"
        assert len(state.report[section]) > 100, f"Section too short: {section}"


def test_pipeline_state_transitions(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    state = run_pipeline(url="https://example.com", dry_run=True)

    # Should end in complete state
    assert state.status == PipelineStatus.COMPLETE
    assert state.error is None
    assert state.elapsed_seconds >= 0
    assert state.cost_usd == 0.0


def test_dry_run_no_real_api_calls(monkeypatch):
    """Ensure dry-run makes zero network calls by unsetting all credentials."""
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    state = run_pipeline(url="https://example.com", dry_run=True)
    assert state.status == PipelineStatus.COMPLETE


def test_parallel_report_sections_calls_generate_section(monkeypatch):
    """Verify _parallel_report_sections exercises generate_section per section."""
    monkeypatch.setenv("DRY_RUN", "true")

    call_log: list[str] = []

    def fake_generate(section: str, analysis: dict) -> str:
        call_log.append(section)
        return f"content for {section}"

    mock_logger = MagicMock()

    with patch("orchestrator.pipeline.ReportWriterAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.generate_section.side_effect = fake_generate

        report = _parallel_report_sections({}, mock_logger)

    expected = ["exec_summary", "current_state", "use_cases", "roadmap", "roi_analysis"]
    assert sorted(call_log) == sorted(expected), f"Expected all 5 sections called, got {call_log}"
    assert sorted(report.keys()) == sorted(expected)
    for section in expected:
        assert report[section] == f"content for {section}"


def test_parallel_report_tolerates_section_failure(monkeypatch):
    """A section that returns AgentError is recorded as None; others still succeed."""
    from agents.base import AgentError

    monkeypatch.setenv("DRY_RUN", "true")

    def fake_generate(section: str, analysis: dict) -> str | AgentError:
        if section == "roi_analysis":
            return AgentError(code="MODEL_FAIL", message="timeout", agent_tag="REPORT")
        return f"ok:{section}"

    mock_logger = MagicMock()

    with patch("orchestrator.pipeline.ReportWriterAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.generate_section.side_effect = fake_generate

        report = _parallel_report_sections({}, mock_logger)

    assert report["roi_analysis"] is None
    assert report["exec_summary"] == "ok:exec_summary"
    assert report["roadmap"] == "ok:roadmap"
