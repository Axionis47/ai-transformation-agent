"""Consultant agent — scores AI maturity and identifies use cases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.base import AgentError, BaseAgent
from ops.model_client import get_model_client

_FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_analysis.json"
_PROMPT = Path(__file__).resolve().parent.parent / "prompts" / "consultant.md"


class ConsultantAgent(BaseAgent):
    """Analyzes company data and produces AI maturity assessment."""

    agent_tag = "CONSULTANT"

    def _run(self, state: Any) -> dict | AgentError:
        if self.dry_run:
            return json.loads(_FIXTURE.read_text())

        company_data = state.company_data if hasattr(state, "company_data") else {}
        rag_context = state.rag_context if hasattr(state, "rag_context") else []

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
        context_str = "\n".join(
            r.get("text", str(r)) if isinstance(r, dict) else str(r)
            for r in rag_context
        )
        return (
            f"Company data:\n{json.dumps(company_data, indent=2)}\n\n"
            f"Similar AI solutions:\n{context_str}\n\n"
            "Produce your analysis as JSON."
        )
