from __future__ import annotations

from typing import Protocol


class GrounderClientProtocol(Protocol):
    """Interface for Gemini grounding calls."""

    def generate_with_grounding(self, prompt: str) -> dict:
        """Call Gemini with GoogleSearch tool. Returns raw API response as dict."""
        ...


class GeminiClient:
    """Vertex AI Gemini client with Google Search grounding. Only file that imports google.genai.

    Two call modes:
    - generate_with_grounding(): attaches GoogleSearch tool, costs budget
    - generate(): pure reasoning, no tools, no budget cost
    """

    def __init__(self, config: dict) -> None:
        # google.genai imported here only — keeps SDK boundary isolated
        import google.genai as genai  # type: ignore[import]
        from google.genai.types import Tool, GoogleSearch, GenerateContentConfig  # type: ignore[import]

        self._Tool = Tool
        self._GoogleSearch = GoogleSearch
        self._GenerateContentConfig = GenerateContentConfig

        models = config.get("models", {})
        gcp = config.get("gcp", {})
        self._model = models.get("grounding_model", "gemini-2.5-flash")
        project = gcp.get("project_id", "plotpointe")
        location = gcp.get("location", "us-central1")

        # ADC: on Cloud Run, credentials come from attached service account
        # via metadata server. No key files or env vars needed.
        self._client = genai.Client(vertexai=True, project=project, location=location)

    def generate(self, prompt: str) -> dict:
        """Pure model call without grounding tools. For reasoning/evaluation steps."""
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        return {"text": response.text or ""}

    def generate_with_grounding(self, prompt: str) -> dict:
        cfg = self._GenerateContentConfig(
            tools=[self._Tool(google_search=self._GoogleSearch())]
        )
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=cfg,
        )
        text = response.text or ""
        raw_meta = getattr(response, "candidates", [])
        grounding_meta: dict = {}
        if raw_meta:
            candidate = raw_meta[0]
            meta = getattr(candidate, "grounding_metadata", None)
            if meta is not None:
                grounding_meta = {
                    "web_search_queries": list(getattr(meta, "web_search_queries", []) or []),
                    "grounding_chunks": [
                        {"web": {"uri": getattr(getattr(c, "web", None), "uri", ""),
                                 "title": getattr(getattr(c, "web", None), "title", "")}}
                        for c in (getattr(meta, "grounding_chunks", []) or [])
                    ],
                    "grounding_supports": [
                        {
                            "segment": {"text": getattr(getattr(s, "segment", None), "text", "")},
                            "grounding_chunk_indices": list(getattr(s, "grounding_chunk_indices", []) or []),
                            "confidence_scores": list(getattr(s, "confidence_scores", []) or []),
                        }
                        for s in (getattr(meta, "grounding_supports", []) or [])
                    ],
                    "search_entry_point": {
                        "rendered_content": getattr(
                            getattr(meta, "search_entry_point", None), "rendered_content", None
                        )
                    },
                }
        return {"text": text, "grounding_metadata": grounding_meta}
