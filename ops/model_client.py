"""Model client abstraction — all LLM calls go through here."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path

from agents.base import AgentError


class ModelClient(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def complete(self, prompt: str, system: str = "", model: str = "") -> str | AgentError:
        """Send a prompt and return the text response."""
        ...


class VertexProvider(ModelClient):
    """Google Vertex AI provider wrapping the Gemini SDK."""

    def __init__(self) -> None:
        self._project = os.getenv("GCP_PROJECT_ID", "")
        self._location = os.getenv("GCP_LOCATION", "us-central1")
        self._default_model = os.getenv("VERTEX_MODEL", "gemini-2.5-pro")
        self._fast_model = os.getenv("VERTEX_FAST_MODEL", "gemini-2.5-flash")
        self._initialized = False

    def _init_vertex(self) -> None:
        if self._initialized:
            return
        from google.cloud import aiplatform  # noqa: local import

        aiplatform.init(project=self._project, location=self._location)
        self._initialized = True

    def complete(self, prompt: str, system: str = "", model: str = "") -> str | AgentError:
        try:
            self._init_vertex()
            from vertexai.generative_models import GenerativeModel  # noqa

            model_name = model or self._default_model
            gen_model = GenerativeModel(model_name, system_instruction=system or None)
            response = gen_model.generate_content(prompt)
            return response.text
        except Exception as exc:
            return AgentError(
                code="MODEL_CALL_FAIL",
                message=f"Vertex AI error: {exc}",
                recoverable=True,
                agent_tag="OPS",
            )


class MockProvider(ModelClient):
    """Returns fixture data for dry-run mode — zero network calls."""

    _FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_analysis.json"

    def complete(self, prompt: str, system: str = "", model: str = "") -> str | AgentError:
        try:
            return self._FIXTURE.read_text()
        except FileNotFoundError:
            return json.dumps({"mock": True, "note": "No fixture file found"})


def get_model_client() -> ModelClient:
    """Factory — returns the correct provider based on env vars."""
    if os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes"):
        return MockProvider()

    provider = os.getenv("MODEL_PROVIDER", "vertex").lower()
    if provider == "vertex":
        return VertexProvider()
    if provider == "mock":
        return MockProvider()

    return MockProvider()
