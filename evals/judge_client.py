"""Judge client — LLM-as-Judge scoring via Anthropic on Vertex AI (evals only)."""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-20250514"
_MAX_TOKENS = 256
_SCORE_PATTERN = re.compile(r"SCORE:\s*([1-5](?:\.\d+)?)")


class JudgeClient:
    """Score outputs against YAML rubrics using an LLM judge (Vertex AI)."""

    def __init__(self) -> None:
        project_id = os.getenv("GCP_PROJECT_ID", "")
        region = os.getenv("GCP_LOCATION", "us-east5")
        if not project_id:
            logger.warning("JudgeClient: GCP_PROJECT_ID not set — scoring unavailable")
            self._available = False
            self._client: Any = None
        else:
            try:
                import anthropic  # noqa: PLC0415
                self._client = anthropic.AnthropicVertex(
                    project_id=project_id,
                    region=region,
                )
                self._available = True
            except ImportError:
                logger.warning("JudgeClient: anthropic package not installed — scoring unavailable")
                self._available = False
                self._client = None

    def score(self, rubric_path: str, output: dict[str, Any]) -> float:
        """Score output against a rubric. Returns 0.0 on any error or unavailability."""
        if not self._available:
            logger.warning("JudgeClient: unavailable, returning 0.0 for %s", rubric_path)
            return 0.0

        try:
            with open(rubric_path, "r") as fh:
                rubric = yaml.safe_load(fh)
        except Exception as exc:
            logger.warning("JudgeClient: failed to load rubric %s: %s", rubric_path, exc)
            return 0.0

        template: str = rubric.get("judge_prompt_template", "")
        if not template:
            logger.warning("JudgeClient: no judge_prompt_template in %s", rubric_path)
            return 0.0

        try:
            prompt = template.format_map(_SafeDict(output))
        except Exception as exc:
            logger.warning("JudgeClient: template substitution failed: %s", exc)
            return 0.0

        try:
            response = self._client.messages.create(
                model=_MODEL,
                max_tokens=_MAX_TOKENS,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
        except Exception as exc:
            logger.warning("JudgeClient: API call failed: %s", exc)
            return 0.0

        match = _SCORE_PATTERN.search(text)
        if not match:
            logger.warning("JudgeClient: no SCORE pattern found in response: %s", text[:120])
            return 0.0

        return min(5.0, max(1.0, float(match.group(1))))


class _SafeDict(dict):  # type: ignore[type-arg]
    """dict subclass that returns empty string for missing keys in format_map."""

    def __missing__(self, key: str) -> str:
        return ""
