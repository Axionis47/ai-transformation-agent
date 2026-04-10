"""Shared factory for Gemini client instances.

Centralises client construction so route files don't cross-import each other.
"""

from __future__ import annotations

import os

from services.grounder.client import GeminiClient
from services.grounder.fake_client import FakeGeminiClient


def build_gemini_client(config: dict) -> object:
    """Return GeminiClient when credentials are available, FakeGeminiClient otherwise.

    For test environments or when Vertex AI is unavailable, falls back to FakeGeminiClient.
    Set USE_FAKE_CLIENT=1 to force fake client (useful for tests).
    """
    if os.getenv("USE_FAKE_CLIENT", "").strip() in ("1", "true"):
        return FakeGeminiClient()
    try:
        return GeminiClient(config=config)
    except Exception:
        return FakeGeminiClient()
