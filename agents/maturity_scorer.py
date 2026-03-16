"""Maturity scorer agent — scores AI maturity from typed signals."""
from __future__ import annotations

import json
import os
from pathlib import Path

from agents.base import AgentError, BaseAgent
from ops.model_client import get_model_client

_FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_maturity.json"
_PROMPT = Path(__file__).resolve().parent.parent / "prompts" / "maturity_scorer.md"


class MaturityScorerAgent(BaseAgent):
    agent_tag = "MATURITY_SCORER"

    def _run(self, input_data: dict) -> dict | AgentError:
        if self.dry_run:
            return json.loads(_FIXTURE.read_text())

        signals = input_data.get("signals", [])
        prompt = self._build_prompt(signals)
        client = get_model_client()
        model = os.getenv("VERTEX_FAST_MODEL", "gemini-2.5-flash")
        response = client.complete(prompt, system=self._load_system_prompt(), model=model)

        if isinstance(response, AgentError):
            return response

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return AgentError(
                code="PARSE_FAIL",
                message="Maturity scorer returned non-JSON",
                recoverable=True,
                agent_tag=self.agent_tag,
            )

    def _load_system_prompt(self) -> str:
        try:
            return _PROMPT.read_text()
        except FileNotFoundError:
            return "Score AI maturity dimensions from typed signals. Return JSON."

    def _build_prompt(self, signals: list) -> str:
        return f"Signals:\n{json.dumps(signals, indent=2)}\n\nScore all four dimensions."
