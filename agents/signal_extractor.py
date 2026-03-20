"""Signal extractor agent — extracts typed signals from raw company data."""
from __future__ import annotations

import json
import os
from pathlib import Path

from agents.base import AgentError, BaseAgent
from ops.model_client import get_model_client

_FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_signals.json"
_PROMPT = Path(__file__).resolve().parent.parent / "prompts" / "signal_extractor.md"


class SignalExtractorAgent(BaseAgent):
    agent_tag = "SIGNAL_EXTRACTOR"

    def _run(self, input_data: dict) -> dict | AgentError:
        if self.dry_run:
            return json.loads(_FIXTURE.read_text())

        company_data = input_data.get("company_data", {})
        prompt = self._build_prompt(company_data)
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
                message="Signal extractor returned non-JSON response",
                recoverable=True,
                agent_tag=self.agent_tag,
            )

    def _load_system_prompt(self) -> str:
        try:
            return _PROMPT.read_text()
        except FileNotFoundError:
            return "Extract factual signals from company website text. Return JSON."

    def _build_prompt(self, company_data: dict) -> str:
        sections = []
        if company_data.get("about_text"):
            sections.append(f"=== ABOUT PAGE ===\n{company_data['about_text'][:3000]}")
        if company_data.get("job_postings"):
            postings = company_data["job_postings"]
            if isinstance(postings, list):
                labelled = [
                    f"[JOB POSTING {i + 1}]\n{str(p)[:600]}"
                    for i, p in enumerate(postings[:15])
                ]
                text = "\n\n".join(labelled)
            else:
                text = str(postings)[:3000]
            sections.append(f"=== JOB POSTINGS ===\n{text}")
        if company_data.get("product_text"):
            sections.append(f"=== PRODUCT/SOLUTIONS PAGE ===\n{company_data['product_text'][:2000]}")
        if company_data.get("blog_text"):
            sections.append(f"=== BLOG / PRESS ===\n{company_data['blog_text'][:2000]}")
        if company_data.get("team_text"):
            sections.append(f"=== TEAM PAGE ===\n{company_data['team_text'][:1500]}")

        if not sections:
            sections.append("No content available.")

        url = company_data.get("url", "unknown")
        return f"Company URL: {url}\n\n" + "\n\n".join(sections) + "\n\nExtract signals as JSON."
