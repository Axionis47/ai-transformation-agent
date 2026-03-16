"""Report writer agent — generates 5-section transformation report."""

from __future__ import annotations

import json
import os
from pathlib import Path
from agents.base import AgentError, BaseAgent
from ops.model_client import get_model_client

_FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_report.json"
_PROMPT = Path(__file__).resolve().parent.parent / "prompts" / "report_writer.md"

REPORT_SECTIONS = ["exec_summary", "current_state", "use_cases", "roadmap", "roi_analysis"]


class ReportWriterAgent(BaseAgent):
    """Generates a 5-section AI transformation report from analysis."""

    agent_tag = "REPORT"

    def generate_section(self, section_name: str, analysis: dict) -> str | AgentError:
        """Generate a single named report section. Used by parallel write path."""
        if section_name not in REPORT_SECTIONS:
            return AgentError(
                code="INVALID_SECTION",
                message=f"Unknown section: {section_name}",
                recoverable=False, agent_tag=self.agent_tag,
            )

        if self.dry_run:
            fixture = json.loads(_FIXTURE.read_text())
            return fixture.get(section_name, "")

        prompt = (
            f"Analysis data:\n{json.dumps(analysis, indent=2)}\n\n"
            f"Generate ONLY the '{section_name}' section of the AI transformation report. "
            "Return plain text (no JSON wrapper)."
        )
        client = get_model_client()
        model = os.getenv("VERTEX_FAST_MODEL", "gemini-2.5-flash")
        response = client.complete(prompt, system=self._load_system_prompt(), model=model)

        if isinstance(response, AgentError):
            return response

        return response.strip()

    def _run(self, input_data: dict) -> dict | AgentError:
        if self.dry_run:
            return json.loads(_FIXTURE.read_text())

        analysis = input_data.get("analysis", {})
        prompt = self._load_prompt(analysis)
        client = get_model_client()
        model = os.getenv("VERTEX_FAST_MODEL", "gemini-2.5-flash")
        response = client.complete(prompt, system=self._load_system_prompt(), model=model)

        if isinstance(response, AgentError):
            return response

        try:
            report = json.loads(response)
        except json.JSONDecodeError:
            return AgentError(
                code="PARSE_FAIL",
                message="Report writer returned non-JSON response",
                recoverable=True, agent_tag=self.agent_tag,
            )

        missing = [s for s in REPORT_SECTIONS if not report.get(s)]
        if missing:
            return AgentError(
                code="INCOMPLETE_REPORT",
                message=f"Missing report sections: {missing}",
                recoverable=True, agent_tag=self.agent_tag,
            )

        return report

    def _load_system_prompt(self) -> str:
        try:
            return _PROMPT.read_text()
        except FileNotFoundError:
            return "You are a report writer for AI transformation consulting."

    def _load_prompt(self, analysis: dict) -> str:
        return (
            f"Analysis data:\n{json.dumps(analysis, indent=2)}\n\n"
            "Generate the 5-section report as JSON."
        )
