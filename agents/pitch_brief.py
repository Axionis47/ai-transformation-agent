"""Pitch brief agent — generates a 5-minute pre-meeting sales brief."""

from __future__ import annotations

import json
import os
from pathlib import Path

from agents.base import AgentError, BaseAgent
from ops.model_client import get_model_client
from orchestrator.question_engine import generate_questions

_PROMPT = Path(__file__).resolve().parent.parent / "prompts" / "pitch_brief.md"

_BRIEF_KEYS = ["opening_line", "story", "roi_conversation", "questions", "objection_prep"]


class PitchBriefAgent(BaseAgent):
    """Generates a pre-meeting pitch brief from pipeline analysis."""

    agent_tag = "PITCH_BRIEF"

    def _run(self, input_data: dict) -> dict | AgentError:
        if self.dry_run:
            return self._dry_run_brief(input_data)

        prompt = self._build_prompt(input_data)
        client = get_model_client()
        model = os.getenv("VERTEX_FAST_MODEL", "gemini-2.5-flash")
        response = client.complete(prompt, system=self._load_system_prompt(), model=model)

        if isinstance(response, AgentError):
            return response

        return self._parse_response(response)

    def _dry_run_brief(self, input_data: dict) -> dict:
        """Build a fixture brief from input data without calling a model."""
        signals = input_data.get("signals") or {}
        match_results = input_data.get("match_results") or {}
        use_cases = input_data.get("use_cases") or []

        delivered = match_results.get("delivered", [])
        top_match = delivered[0] if delivered else {}
        top_uc = use_cases[0] if use_cases else {}

        pain_signals = [
            s for s in signals.get("signals", []) if s.get("type") == "pain_point"
        ]
        pain_value = pain_signals[0].get("value", "operational inefficiency") if pain_signals else "operational inefficiency"

        proven = top_match.get("proven_metrics") or {}
        metric_val = proven.get("primary_value", "25% efficiency improvement")
        metric_label = proven.get("primary_label", "efficiency gain")

        engagement_title = top_match.get("source_title", "a similar engagement")
        client_profile = top_match.get("client_profile_summary", "a company with a similar profile")
        tech_approach = top_match.get("tech_approach", "an ML-based automation layer")
        duration = top_match.get("engagement_duration") or 6

        questions = generate_questions(match_results, signals)
        question_texts = [q["question"] for q in questions]

        roi_estimate = top_uc.get("roi_estimate", "15-25% cost reduction")

        return {
            "opening_line": (
                f"You're spending significant resources on {pain_value}. "
                f"We've delivered {metric_val} {metric_label} for a company with your exact profile."
            ),
            "story": (
                f"We worked with {client_profile} through {engagement_title}. "
                f"They faced the same challenge with {pain_value}. "
                f"We built {tech_approach}. "
                f"In {duration} months, they achieved {metric_val} {metric_label}."
            ),
            "roi_conversation": (
                f"1. Their probable cost: confirm baseline in meeting.\n"
                f"2. Delivered result: {metric_val} {metric_label} (proven).\n"
                f"3. Estimated savings: {roi_estimate}.\n"
                f"4. Engagement scope: {duration} months.\n"
                f"5. Payback period: confirm in meeting."
            ),
            "questions": question_texts,
            "objection_prep": (
                "We tried this before: Ask what failed before responding.\n"
                f"Timeline concerns: Our typical engagement is {duration} months.\n"
                "We don't have the team: confirm team involvement requirements in meeting."
            ),
        }

    def _load_system_prompt(self) -> str:
        try:
            return _PROMPT.read_text()
        except FileNotFoundError:
            return "You are a sales preparation assistant. Generate a 5-minute pitch brief as JSON."

    def _build_prompt(self, input_data: dict) -> str:
        return (
            f"Analysis data:\n{json.dumps(input_data, indent=2)}\n\n"
            "Generate the pitch brief as JSON with keys: "
            "opening_line, story, roi_conversation, questions, objection_prep."
        )

    def _parse_response(self, response: str) -> dict | AgentError:
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        try:
            brief = json.loads(text)
        except json.JSONDecodeError:
            return AgentError(
                code="PARSE_FAIL",
                message="Pitch brief returned non-JSON response",
                recoverable=True,
                agent_tag=self.agent_tag,
            )
        missing = [k for k in _BRIEF_KEYS if k not in brief]
        if missing:
            return AgentError(
                code="INCOMPLETE_BRIEF",
                message=f"Missing brief sections: {missing}",
                recoverable=True,
                agent_tag=self.agent_tag,
            )
        return brief
