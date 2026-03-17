"""Judge client — LLM-as-Judge scoring via Vertex AI Gemini (evals only)."""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_MODEL = os.getenv("EVAL_JUDGE_MODEL", "gemini-2.5-pro")
_MAX_TOKENS = 256
_SCORE_PATTERN = re.compile(r"SCORE:\s*([1-5](?:\.\d+)?)")

# Hardcoded GCP config — no env var exporting needed
_GCP_PROJECT = "plotpointe"
_GCP_LOCATION = "us-central1"


class JudgeClient:
    """Score outputs against YAML rubrics using Gemini on Vertex AI."""

    def __init__(self) -> None:
        try:
            from vertexai.generative_models import GenerativeModel  # noqa
            from google.cloud import aiplatform
            aiplatform.init(
                project=os.getenv("GCP_PROJECT_ID", _GCP_PROJECT),
                location=os.getenv("GCP_LOCATION", _GCP_LOCATION),
            )
            self._available = True
        except Exception as exc:
            logger.warning("JudgeClient: Vertex AI init failed: %s", exc)
            self._available = False

    def score(self, rubric_path: str, output: dict[str, Any]) -> float:
        """Score output against a rubric. Returns 0.0 on error."""
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
            from vertexai.generative_models import GenerationConfig, GenerativeModel
            model = GenerativeModel(_MODEL)
            config = GenerationConfig(max_output_tokens=_MAX_TOKENS, temperature=0)
            response = model.generate_content(prompt, generation_config=config)
            text = response.text
        except Exception as exc:
            logger.warning("JudgeClient: API call failed: %s", exc)
            return 0.0

        match = _SCORE_PATTERN.search(text)
        if not match:
            logger.warning("JudgeClient: no SCORE pattern in response: %s", text[:120])
            return 0.0

        return min(5.0, max(1.0, float(match.group(1))))


class _SafeDict(dict):  # type: ignore[type-arg]
    """dict subclass that returns empty string for missing keys in format_map."""

    def __missing__(self, key: str) -> str:
        return ""
