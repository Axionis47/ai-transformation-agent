"""Use case generator agent — produces three-tier AI recommendations."""
from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from agents.base import AgentError, BaseAgent
from ops.model_client import get_model_client

_FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_use_cases.json"
_PROMPT = Path(__file__).resolve().parent.parent / "prompts" / "use_case_generator.md"
_TIER_PROMPTS: dict[str, Path] = {
    "delivered": Path(__file__).resolve().parent.parent / "prompts" / "tier1_delivered.md",
    "adaptation": Path(__file__).resolve().parent.parent / "prompts" / "tier2_adaptation.md",
    "ambitious": Path(__file__).resolve().parent.parent / "prompts" / "tier3_ambitious.md",
}

class UseCaseGeneratorAgent(BaseAgent):
    agent_tag = "USE_CASE_GENERATOR"

    def _run(self, input_data: dict) -> list | AgentError:
        if self.dry_run:
            return json.loads(_FIXTURE.read_text())

        match_results: dict | None = input_data.get("match_results")
        signals = input_data.get("signals", [])
        maturity = input_data.get("maturity", {})
        victory_matches = input_data.get("victory_matches", [])

        if match_results:
            return self._synthesize_per_tier(signals, maturity, match_results)

        # Backwards compat: single-prompt synthesis when match_results not provided
        prompt = self._build_prompt(signals, maturity, victory_matches)
        client = get_model_client()
        model = os.getenv("VERTEX_MODEL", "gemini-2.5-pro")
        response = client.complete(prompt, system=self._load_system_prompt(), model=model)

        if isinstance(response, AgentError):
            return response

        return self._parse_response(response)

    def _synthesize_per_tier(
        self, signals: list, maturity: dict, match_results: dict
    ) -> list | AgentError:
        """Make up to 3 model calls, one per non-empty tier, then combine."""
        client = get_model_client()
        model = os.getenv("VERTEX_MODEL", "gemini-2.5-pro")

        def _call_tier(tier_key: str, records: list) -> tuple[str, list | AgentError]:
            system = self._load_tier_prompt(tier_key)
            prompt = self._build_tier_prompt(signals, maturity, records, tier_key)
            response = client.complete(prompt, system=system, model=model)
            if isinstance(response, AgentError):
                return tier_key, response
            parsed = self._parse_response(response)
            return tier_key, parsed

        active_tiers = {k: v for k, v in match_results.items() if v}
        if not active_tiers:
            return self._fallback_ambitious(signals, maturity, client, model)

        tier_results: dict[str, list] = {}
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {
                pool.submit(_call_tier, k, v): k for k, v in active_tiers.items()
            }
            for future in as_completed(futures):
                tier_key, result = future.result()
                if isinstance(result, AgentError):
                    tier_results[tier_key] = []
                else:
                    tier_results[tier_key] = result

        combined: list = []
        for tier_key in ("delivered", "adaptation", "ambitious"):
            combined.extend(tier_results.get(tier_key, []))

        if not combined:
            return self._fallback_ambitious(signals, maturity, client, model)
        return combined

    def _fallback_ambitious(
        self, signals: list, maturity: dict, client: object, model: str
    ) -> list | AgentError:
        """Return a single AMBITIOUS use case from general industry signals."""
        system = self._load_tier_prompt("ambitious")
        prompt = self._build_tier_prompt(signals, maturity, [], "ambitious")
        response = client.complete(prompt, system=system, model=model)
        if isinstance(response, AgentError):
            return response
        return self._parse_response(response)

    def _load_tier_prompt(self, tier_key: str) -> str:
        path = _TIER_PROMPTS.get(tier_key)
        if path and path.exists():
            return path.read_text()
        return self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        try:
            return _PROMPT.read_text()
        except FileNotFoundError:
            return "Generate three-tier AI use cases. Return JSON array."

    def _build_tier_prompt(
        self, signals: list, maturity: dict, records: list, tier_key: str
    ) -> str:
        return (
            f"Signals:\n{json.dumps(signals, indent=2)}\n\n"
            f"Maturity assessment:\n{json.dumps(maturity, indent=2)}\n\n"
            f"match_results ({tier_key}):\n{json.dumps(records, indent=2)}\n\n"
            "Generate use cases as a JSON array."
        )

    def _extract_json(self, text: str) -> str:
        """Strip markdown code fences if present."""
        import re
        match = re.search(r'```(?:json)?\s*\n(.*?)```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()

    def _parse_response(self, response: str) -> list:
        try:
            cleaned = self._extract_json(response)
            result = json.loads(cleaned)
            return result if isinstance(result, list) else result.get("use_cases", [result])
        except json.JSONDecodeError:
            return []

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
