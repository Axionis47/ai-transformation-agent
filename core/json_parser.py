"""Extract JSON from LLM responses that may include markdown code blocks."""
from __future__ import annotations

import json
import re


def extract_json(text: str) -> dict:
    """Parse JSON from model output, handling markdown code fences."""
    # Try stripping markdown code blocks first
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    candidate = match.group(1).strip() if match else text.strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    # Fallback: find first { ... } block
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass
    return {}
