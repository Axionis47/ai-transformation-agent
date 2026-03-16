"""Use case generator agent — produces three-tier AI recommendations."""
from __future__ import annotations

import json
import os
from pathlib import Path

from agents.base import AgentError, BaseAgent
from ops.model_client import get_model_client

_FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_use_cases.json"
_PROMPT = Path(__file__).resolve().parent.parent / "prompts" / "use_case_generator.md"


class UseCaseGeneratorAgent(BaseAgent):
    agent_tag = "USE_CASE_GENERATOR"

    def _run(self, input_data: dict) -> list | AgentError:
        if self.dry_run:
            return json.loads(_FIXTURE.read_text())

        signals = input_data.get("signals", [])
        maturity = input_data.get("maturity", {})
        victory_matches = input_data.get("victory_matches", [])

        prompt = self._build_prompt(signals, maturity, victory_matches)
        client = get_model_client()
        model = os.getenv("VERTEX_MODEL", "gemini-2.5-pro")
        response = client.complete(prompt, system=self._load_system_prompt(), model=model)

        if isinstance(response, AgentError):
            return response

        try:
            result = json.loads(response)
            return result if isinstance(result, list) else result.get("use_cases", [result])
        except json.JSONDecodeError:
            return AgentError(
                code="PARSE_FAIL",
                message="Use case generator returned non-JSON",
                recoverable=True,
                agent_tag=self.agent_tag,
            )

    def _load_system_prompt(self) -> str:
        try:
            return _PROMPT.read_text()
        except FileNotFoundError:
            return "Generate three-tier AI use cases. Return JSON array."

    def _build_prompt(self, signals: list, maturity: dict, victory_matches: list) -> str:
        gap_lines = []
        for vm in victory_matches:
            gap = vm.get("gap_analysis") if isinstance(vm, dict) else getattr(vm, "gap_analysis", None)
            if gap:
                title = vm.get("engagement_title") if isinstance(vm, dict) else getattr(vm, "engagement_title", "")
                gap_lines.append(f"- {title}: {gap}")
        gap_section = (
            "\n\nGap analysis from matched victories:\n" + "\n".join(gap_lines)
            if gap_lines else ""
        )
        return (
            f"Signals:\n{json.dumps(signals, indent=2)}\n\n"
            f"Maturity assessment:\n{json.dumps(maturity, indent=2)}\n\n"
            f"Tenex victory matches:\n{json.dumps(victory_matches, indent=2)}"
            f"{gap_section}\n\n"
            "Generate use cases as a JSON array."
        )
