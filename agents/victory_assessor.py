"""Victory assessor agent — per-victory LLM assessment against session state."""
from __future__ import annotations

import json
import os
from pathlib import Path

from agents.base import AgentError, BaseAgent
from ops.model_client import get_model_client

_PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "victory_assessor.md"


_VICTORY_QUESTIONS: dict[str, str] = {
    "invoice": "What ERP do they use? That determines integration path.",
    "compliance": "Which regulatory frameworks apply? (OCC, FDIC, SEC, state?)",
    "contract": "What contract volume do they handle monthly?",
    "support": "What's their current ticket volume and resolution time?",
    "knowledge": "How many internal documents would this need to cover?",
    "clinical": "What EHR system are they on?",
    "product": "How many SKUs need descriptions?",
    "demand": "What's their forecasting cycle? Monthly, weekly?",
    "document": "What document types and what monthly volume?",
    "sales": "What CRM do they use? Salesforce, HubSpot?",
    "quality": "What's their current defect rate and inspection method?",
}


def _compute_scaled_value(
    savings_text: str, scale: float, metric_value: str,
    v_employees: int, c_employees: int,
) -> str:
    """Try to compute an actual dollar estimate from savings text."""
    import re as _re
    # Try to extract dollar amount from savings text like "$340K/year"
    dollar_match = _re.search(r"\$(\d+(?:\.\d+)?)\s*([KkMm])?", savings_text)
    if dollar_match:
        amount = float(dollar_match.group(1))
        suffix = (dollar_match.group(2) or "").upper()
        if suffix == "K":
            amount *= 1_000
        elif suffix == "M":
            amount *= 1_000_000
        scaled = amount * scale
        if scaled >= 1_000_000:
            return f"${scaled / 1_000_000:.1f}M/year"
        if scaled >= 1_000:
            return f"${int(scaled / 1_000)}K/year"
        return f"${int(scaled)}/year"

    # Try percentage from metric_value
    pct_match = _re.search(r"(\d+(?:\.\d+)?)\s*%", metric_value)
    if pct_match:
        return f"{metric_value} (proven at {v_employees} employees, applicable at {c_employees})"

    # Fallback: describe the scaling
    return f"{metric_value} at {scale}x scale ({c_employees} employees)"


def _pick_question(title: str, c_tech: list[str]) -> str:
    """Pick a contextually relevant question based on victory type."""
    title_lower = title.lower()
    for keyword, question in _VICTORY_QUESTIONS.items():
        if keyword in title_lower:
            return question
    return "What's their timeline and budget appetite for this kind of initiative?"


def _truncate_sentence(text: str, max_len: int = 250) -> str:
    """Truncate text at the last sentence boundary before max_len."""
    if len(text) <= max_len:
        return text
    truncated = text[:max_len]
    last_period = truncated.rfind(".")
    if last_period > max_len // 2:
        return truncated[: last_period + 1]
    return truncated.rstrip() + "..."


def _assess_dry_run(victory: dict, company: dict) -> dict:
    """Build a realistic assessment from actual victory data without LLM."""
    vid = victory.get("id", "")
    title = victory.get("engagement_title", "")
    v_industry = victory.get("industry", "")
    c_industry = company.get("industry", "")
    c_pains = company.get("pain_points", [])
    c_emp = company.get("employee_count")
    c_tech = company.get("known_tech", [])

    results = victory.get("results", {})
    pm = results.get("primary_metric", {}) if isinstance(results, dict) else {}
    metric_label = pm.get("label", "")
    metric_value = pm.get("value", "")
    secondary = results.get("secondary_metrics", []) if isinstance(results, dict) else []
    savings_text = secondary[0].get("value", "") if secondary else ""

    profile = victory.get("company_profile", {}) if isinstance(victory.get("company_profile"), dict) else {}
    v_employees = profile.get("size_employees", 0)
    problem = victory.get("problem_statement", "")
    solution = victory.get("solution_summary", "")

    # Tier classification
    same_industry = v_industry.lower() == c_industry.lower()
    pain_overlap = any(
        any(word in pain.lower() for word in title.lower().split())
        for pain in c_pains
    ) if c_pains else False

    if same_industry and pain_overlap:
        tier, confidence = "EASY_WIN", 0.88
    elif same_industry:
        tier, confidence = "EASY_WIN", 0.78
    elif pain_overlap:
        tier, confidence = "MODERATE_WIN", 0.68
    else:
        tier, confidence = "MODERATE_WIN", 0.55

    # ROI calibration using actual metrics with computed dollar values
    calibration = None
    if c_emp and v_employees and v_employees > 0:
        scale = round(c_emp / v_employees, 1)
        estimated = _compute_scaled_value(savings_text, scale, metric_value, v_employees, c_emp)
        calibration = {
            "victory_metric": f"{metric_label}: {metric_value}",
            "victory_savings": savings_text or f"{metric_value} at {v_employees} employees",
            "scale_factor": scale,
            "estimated_value": estimated,
            "basis": f"Scaled from {v_employees} to {c_emp} employees ({scale}x)",
            "confidence_note": "Assumes similar operational density per employee",
        }

    # Prerequisites: use client_systems_integrated, not cloud infra
    tech = victory.get("tech_stack", {}) if isinstance(victory.get("tech_stack"), dict) else {}
    client_systems = tech.get("client_systems_integrated", [])
    if isinstance(client_systems, list) and client_systems:
        prereq_items = client_systems[:3]
    else:
        prereq_items = [f"{v_industry} domain expertise", "Data access"]

    c_tech_lower = {t.lower() for t in c_tech}
    confirmed, missing = [], []
    for item in prereq_items:
        if any(t in str(item).lower() for t in c_tech_lower):
            confirmed.append(f"{item} (analyst confirmed)")
        else:
            missing.append(f"{item} not confirmed")

    if same_industry:
        confirmed.append(f"{v_industry} industry match")

    # Problem fit citing specific pain points
    matching_pain = next(
        (p for p in c_pains if any(w in p.lower() for w in title.lower().split() if len(w) > 3)),
        None,
    )
    if matching_pain:
        problem_fit = f'Direct match: analyst cited "{matching_pain}"'
    elif same_industry:
        problem_fit = f"Same industry ({v_industry}). {problem[:100]}"
    else:
        problem_fit = f"Pattern from {v_industry} may transfer. {problem[:80]}"

    return {
        "victory_id": vid,
        "victory_title": title,
        "tier": tier,
        "confidence": confidence,
        "what_we_did": _truncate_sentence(solution or problem),
        "problem_fit": problem_fit,
        "confirmed": confirmed,
        "missing": missing,
        "calibration": calibration,
        "adaptation_notes": "" if tier == "EASY_WIN" else f"Base solution from {v_industry}; core approach transfers but {c_industry} context needs adaptation",
        "key_question": _pick_question(title, c_tech),
    }


class VictoryAssessorAgent(BaseAgent):
    """Assess how well a single victory fits the current prospect."""

    agent_tag = "VICTORY_ASSESSOR"

    def _run(self, input_data: dict) -> dict | AgentError:
        victory: dict = input_data.get("victory", {})
        company: dict = input_data.get("company", {})

        if not victory:
            return AgentError(
                code="NO_VICTORY",
                message="No victory record provided",
                recoverable=True,
                agent_tag=self.agent_tag,
            )

        if self.dry_run:
            return _assess_dry_run(victory, company)

        system_prompt = _PROMPT_FILE.read_text()
        user_prompt = (
            f"Victory record:\n{json.dumps(victory, indent=2)}\n\n"
            f"Company context:\n{json.dumps(company, indent=2)}"
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
                message=f"Failed to parse assessment: {raw[:200]}",
                recoverable=True,
                agent_tag=self.agent_tag,
            )
