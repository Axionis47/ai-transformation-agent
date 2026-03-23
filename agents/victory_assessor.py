"""Victory assessor agent — per-victory LLM assessment against session state."""
from __future__ import annotations

import json
import os
from pathlib import Path

from agents.base import AgentError, BaseAgent
from ops.model_client import get_model_client

_PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "victory_assessor.md"
_FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_victory_assessment.json"


class VictoryAssessorAgent(BaseAgent):
    """Assess how well a single victory fits the current prospect."""

    agent_tag = "VICTORY_ASSESSOR"

    def _run(self, input_data: dict) -> dict | AgentError:
        victory: dict = input_data.get("victory", {})
        company: dict = input_data.get("company", {})

        if not victory:
            return AgentError(
                code="NO_VICTORY",
                message="No victory record provided",
                recoverable=True,
                agent_tag=self.agent_tag,
            )

        if self.dry_run:
            fixture = json.loads(_FIXTURE.read_text())
            fixture["victory_id"] = victory.get("id", fixture.get("victory_id", ""))
            fixture["victory_title"] = victory.get(
                "engagement_title", fixture.get("victory_title", ""),
            )
            return fixture

        system_prompt = _PROMPT_FILE.read_text()
        user_prompt = (
            f"Victory record:\n{json.dumps(victory, indent=2)}\n\n"
            f"Company context:\n{json.dumps(company, indent=2)}"
        )

        model = os.getenv("VERTEX_FAST_MODEL", "gemini-2.5-flash")
        client = get_model_client()
        raw = client.complete(prompt=user_prompt, system=system_prompt, model=model)
        if isinstance(raw, AgentError):
            return raw

        try:
            parsed = json.loads(raw)
            return parsed
        except (json.JSONDecodeError, TypeError):
            return AgentError(
                code="PARSE_FAIL",
                message=f"Failed to parse assessment: {raw[:200]}",
                recoverable=True,
                agent_tag=self.agent_tag,
            )
