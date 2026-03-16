"""Consultant agent — scores AI maturity and identifies use cases."""

from __future__ import annotations

import json
from pathlib import Path
from agents.base import AgentError, BaseAgent
from ops.model_client import get_model_client

_FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_analysis.json"
_PROMPT = Path(__file__).resolve().parent.parent / "prompts" / "consultant.md"


def format_wins(rag_context: list) -> str:
    """Format RAG victory records as structured win summaries.

    Handles both full victory records (nested dicts from victories.json)
    and flat ChromaDB metadata results.
    """
    if not rag_context:
        return "No relevant Tenex delivery wins found."

    parts: list[str] = []
    for win in rag_context:
        win_id = win.get("id", "unknown")
        title = win.get("engagement_title", "Untitled")
        industry = win.get("industry", "unknown")

        # company_profile — nested dict (full record) or flat fields (ChromaDB)
        profile = win.get("company_profile")
        if isinstance(profile, dict):
            size = profile.get("size_label", "")
        else:
            size = win.get("size_label", "")

        maturity = win.get("maturity_at_engagement", "")

        # results — nested dict (full record) or flat fields (ChromaDB)
        results = win.get("results")
        if isinstance(results, dict) and results:
            pm = results.get("primary_metric", {})
            metric_label = pm.get("label", "")
            metric_value = pm.get("value", "")
            baseline = pm.get("baseline", "")
            outcome = pm.get("outcome", "")
            period = results.get("measurement_period", "")
        else:
            metric_label = win.get("primary_metric_label", "")
            metric_value = win.get("primary_metric_value", "")
            baseline = ""
            outcome = ""
            period = win.get("measurement_period", "")

        # engagement_details — nested dict or flat
        details = win.get("engagement_details", {})
        if isinstance(details, dict):
            duration = details.get("duration_months", win.get("duration_months", ""))
            team = details.get("tenex_team_size", "")
        else:
            duration = win.get("duration_months", "")
            team = ""

        problem = win.get("problem_statement", "")[:200]
        solution = win.get("solution_summary", "")[:200]

        result_line = f"{metric_label}: {metric_value}"
        if baseline and outcome:
            result_line += f" ({baseline} → {outcome})"
        if period:
            result_line += f" — {period}"

        block = (
            f"{win_id} — {title}\n"
            f"  Industry: {industry} | Size: {size} | Maturity at engagement: {maturity}\n"
            f"  Problem: {problem}\n"
            f"  Solution: {solution}\n"
            f"  Primary result: {result_line}\n"
            f"  Duration: {duration} months | Team: {team} Tenex engineers"
        )
        parts.append(block)

    return "\n\n".join(parts)


class ConsultantAgent(BaseAgent):
    """Analyzes company data and produces AI maturity assessment."""

    agent_tag = "CONSULTANT"

    def _run(self, input_data: dict) -> dict | AgentError:
        if self.dry_run:
            return json.loads(_FIXTURE.read_text())

        company_data = input_data.get("company_data", {})
        rag_context = input_data.get("rag_context", [])

        prompt = self._load_prompt(company_data, rag_context)
        client = get_model_client()
        response = client.complete(prompt, system=self._load_system_prompt())

        if isinstance(response, AgentError):
            return response

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return AgentError(
                code="PARSE_FAIL",
                message="Consultant model returned non-JSON response",
                recoverable=True, agent_tag=self.agent_tag,
            )

    def _load_system_prompt(self) -> str:
        try:
            return _PROMPT.read_text()
        except FileNotFoundError:
            return "You are an AI transformation consultant."

    def _load_prompt(self, company_data: dict, rag_context: list) -> str:
        wins_str = format_wins(rag_context)
        return (
            f"Company data:\n{json.dumps(company_data, indent=2)}\n\n"
            f"Relevant Tenex delivery wins:\n{wins_str}\n\n"
            "Produce your analysis as JSON."
        )
