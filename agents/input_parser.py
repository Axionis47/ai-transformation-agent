"""Input parser agent — extracts structured data from analyst free text."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from agents.base import AgentError, BaseAgent
from ops.model_client import get_model_client

_PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "input_parser.md"
_FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_parsed_input.json"

_KNOWN_TECH = [
    "SAP", "Oracle", "Salesforce", "Workday", "NetSuite", "PostgreSQL",
    "MySQL", "MongoDB", "Snowflake", "BigQuery", "AWS", "Azure", "GCP",
    "Kubernetes", "Docker", "Tableau", "Power BI", "Jira", "Confluence",
]


def _dry_run_parse(message: str) -> dict:
    """Simple keyword extraction for dry-run mode."""
    msg_lower = message.lower()
    if "generate pitch" in msg_lower or "create pitch" in msg_lower:
        return {"generate_pitch": True}

    result: dict = {
        "company_name": "", "industry": "", "size_label": "",
        "employee_count": None, "pain_points": [], "known_tech": [],
        "manual_processes": [], "context_notes": [], "explicit_queries": [],
        "generate_pitch": False,
    }

    tech_found = [t for t in _KNOWN_TECH if t.lower() in msg_lower]
    if tech_found:
        result["known_tech"] = tech_found

    emp_match = re.search(r"~?(\d[\d,]*)\s*employees", message, re.IGNORECASE)
    if emp_match:
        result["employee_count"] = int(emp_match.group(1).replace(",", ""))

    if "?" in message:
        for sentence in message.split("."):
            if "?" in sentence:
                result["explicit_queries"].append(sentence.strip().rstrip("?") + "?")

    ctx_keywords = ["BaaS", "regulated", "OCC", "FDIC", "fintech", "SaaS"]
    for kw in ctx_keywords:
        if kw.lower() in msg_lower:
            result["context_notes"].append(kw)

    return result


class InputParserAgent(BaseAgent):
    """Parse analyst messages into structured session updates."""

    agent_tag = "INPUT_PARSER"

    def _run(self, input_data: dict) -> dict | AgentError:
        message: str = input_data.get("message", "")
        session_summary: str = input_data.get("session_summary", "")
        is_first_turn: bool = input_data.get("is_first_turn", False)

        if not message.strip():
            return AgentError(
                code="EMPTY_INPUT",
                message="Analyst message is empty",
                recoverable=True,
                agent_tag=self.agent_tag,
            )

        if self.dry_run:
            if is_first_turn:
                return json.loads(_FIXTURE.read_text())
            return _dry_run_parse(message)

        system_prompt = _PROMPT_FILE.read_text()
        user_prompt = (
            f"Current session state:\n{session_summary}\n\n"
            f"Analyst message:\n{message}"
        )

        model = os.getenv("VERTEX_FAST_MODEL", "gemini-2.5-flash")
        client = get_model_client()
        raw = client.complete(prompt=user_prompt, system=system_prompt, model=model)
        if isinstance(raw, AgentError):
            return raw

        try:
            parsed = json.loads(raw)
            return parsed
        except (json.JSONDecodeError, TypeError):
            return AgentError(
                code="PARSE_FAIL",
                message=f"Failed to parse model output as JSON: {raw[:200]}",
                recoverable=True,
                agent_tag=self.agent_tag,
            )
