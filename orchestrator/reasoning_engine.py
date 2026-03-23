"""Reasoning engine — processes each analyst turn and updates session state."""
from __future__ import annotations

import json
import os
from pathlib import Path

from agents.base import AgentError
from agents.input_parser import InputParserAgent
from agents.victory_assessor import VictoryAssessorAgent
from ops.model_client import get_model_client
from orchestrator.session_schemas import (
    ParsedInput,
    Recommendations,
    SessionState,
    TargetedQuestion,
    Turn,
    VictoryAssessment,
)
from services.victory_service import VictoryService

_RESPONSE_PROMPT = Path(__file__).resolve().parent.parent / "prompts" / "response_formatter.md"


def _session_summary(state: SessionState) -> str:
    """Build a compact text summary of the current session for LLM context."""
    parts = [f"Company: {state.company_name or 'unknown'}"]
    if state.industry:
        parts.append(f"Industry: {state.industry}")
    if state.size_label:
        parts.append(f"Size: {state.size_label}")
    if state.employee_count:
        parts.append(f"Employees: {state.employee_count}")
    if state.pain_points:
        parts.append(f"Pain points: {', '.join(state.pain_points)}")
    if state.known_tech:
        parts.append(f"Tech: {', '.join(state.known_tech)}")
    if state.context_notes:
        parts.append(f"Context: {', '.join(state.context_notes)}")
    return "\n".join(parts)


def _company_context(state: SessionState) -> dict:
    """Build the company context dict for the victory assessor."""
    return {
        "company_name": state.company_name,
        "industry": state.industry,
        "size_label": state.size_label,
        "employee_count": state.employee_count,
        "pain_points": state.pain_points,
        "known_tech": state.known_tech,
        "manual_processes": state.manual_processes,
        "context_notes": state.context_notes,
    }


def _merge_new_info(state: SessionState, parsed: dict) -> dict:
    """Merge parsed input into session state. Returns dict of what changed."""
    changes: dict = {}
    if parsed.get("company_name") and not state.company_name:
        state.company_name = parsed["company_name"]
        changes["company_name"] = state.company_name
    if parsed.get("industry") and not state.industry:
        state.industry = parsed["industry"]
        changes["industry"] = state.industry
    if parsed.get("size_label") and not state.size_label:
        state.size_label = parsed["size_label"]
        changes["size_label"] = state.size_label
    if parsed.get("employee_count") and not state.employee_count:
        state.employee_count = parsed["employee_count"]
        changes["employee_count"] = state.employee_count

    new_pain = [p for p in parsed.get("pain_points", []) if p not in state.pain_points]
    if new_pain:
        state.pain_points.extend(new_pain)
        changes["new_pain_points"] = new_pain

    new_tech = [t for t in parsed.get("known_tech", []) if t not in state.known_tech]
    if new_tech:
        state.known_tech.extend(new_tech)
        changes["new_tech"] = new_tech

    new_procs = [
        m for m in parsed.get("manual_processes", [])
        if m not in state.manual_processes
    ]
    if new_procs:
        state.manual_processes.extend(new_procs)
        changes["new_processes"] = new_procs

    new_ctx = [
        c for c in parsed.get("context_notes", [])
        if c not in state.context_notes
    ]
    if new_ctx:
        state.context_notes.extend(new_ctx)
        changes["new_context"] = new_ctx

    return changes


def _assess_victory(victory: dict, state: SessionState) -> VictoryAssessment | None:
    """Run the VictoryAssessorAgent on a single victory record."""
    agent = VictoryAssessorAgent()
    result = agent.run({
        "victory": victory,
        "company": _company_context(state),
        "dry_run": state.dry_run,
    })
    if isinstance(result, AgentError):
        return None
    try:
        return VictoryAssessment(**result)
    except Exception:
        return None


def _already_matched(state: SessionState, victory_id: str) -> bool:
    """Check if a victory is already in the matched list."""
    return any(v.victory_id == victory_id for v in state.matched_victories)


def classify_recommendations(assessments: list[VictoryAssessment]) -> Recommendations:
    """Sort assessments into three tiers."""
    easy = [a for a in assessments if a.tier == "EASY_WIN"]
    moderate = [a for a in assessments if a.tier == "MODERATE_WIN"]
    ambitious = [a for a in assessments if a.tier == "AMBITIOUS"]

    easy.sort(key=lambda a: -a.confidence)
    moderate.sort(key=lambda a: -a.confidence)
    ambitious.sort(key=lambda a: -a.confidence)

    questions = []
    for a in assessments:
        if a.key_question and a.missing:
            questions.append(TargetedQuestion(
                question=a.key_question,
                why=f"Needed for {a.victory_title}",
                victory_id=a.victory_id,
                field=a.missing[0] if a.missing else "",
            ))
    questions = questions[:3]

    return Recommendations(
        easy_wins=easy,
        moderate_wins=moderate,
        ambitious=ambitious,
        top_questions=questions,
    )


def _format_response(
    state: SessionState, changes: dict, new_assessments: list[VictoryAssessment],
) -> str:
    """Format the system response using the response formatter prompt."""
    if state.dry_run:
        parts = []
        if changes.get("new_tech"):
            parts.append(f"Noted: {', '.join(changes['new_tech'])} confirmed.")
            # Report prerequisite updates
            for a in state.matched_victories:
                if any("confirmed" in c for c in a.confirmed):
                    parts.append(f"  {a.victory_title}: prerequisites updated.")
            parts.append("")
        if changes.get("new_context"):
            parts.append(f"Context updated: {', '.join(changes['new_context'])}")
            parts.append("")
        if new_assessments:
            for a in new_assessments:
                tier_label = a.tier.replace("_", " ")
                parts.append(f"{tier_label}: {a.victory_title} ({a.victory_id})")
                if a.what_we_did:
                    parts.append(f"  {a.what_we_did}")
                if a.calibration and a.calibration.estimated_value:
                    parts.append(f"  Estimated value: {a.calibration.estimated_value}")
                if a.key_question:
                    parts.append(f"  > {a.key_question}")
                parts.append("")
        if not new_assessments and not changes:
            parts.append("No new matches. Try adding more pain points or context.")
        if state.questions_pending:
            for q in state.questions_pending[:2]:
                parts.append(f"Question: {q.question}")
        return "\n".join(parts) if parts else "Session started. What can you tell me about this company?"

    prompt_text = _RESPONSE_PROMPT.read_text()
    context = json.dumps({
        "new_assessments": [a.model_dump() for a in new_assessments],
        "recommendations": state.recommendations.model_dump() if state.recommendations else {},
        "questions": [q.model_dump() for q in state.questions_pending[:3]],
        "state_changes": changes,
    }, indent=2)

    model = os.getenv("VERTEX_FAST_MODEL", "gemini-2.5-flash")
    client = get_model_client()
    raw = client.complete(prompt=context, system=prompt_text, model=model)
    if isinstance(raw, AgentError):
        return f"I found {len(new_assessments)} matches but had trouble formatting. Raw data available."
    return raw.strip().strip('"')


def process_turn(state: SessionState, analyst_message: str) -> str:
    """Process one analyst message, update state, return system response."""
    # Check for pitch command in raw message first
    if analyst_message.strip().lower() in ("generate pitch", "create pitch"):
        return _generate_pitch(state)

    # 1. Parse analyst input
    is_first = len(state.turn_history) == 0
    parser = InputParserAgent()
    parsed = parser.run({
        "message": analyst_message,
        "session_summary": _session_summary(state),
        "dry_run": state.dry_run,
        "is_first_turn": is_first,
    })
    if isinstance(parsed, AgentError):
        return f"I couldn't parse that message: {parsed.message}"

    # Check for pitch generation request from parser
    if parsed.get("generate_pitch"):
        return _generate_pitch(state)

    # 2. Merge new info into state
    changes = _merge_new_info(state, parsed)

    # 3. Record the analyst turn
    state.turn_history.append(Turn(
        role="analyst", content=analyst_message, state_changes=changes,
    ))

    # 4. Query RAG for new matches based on changes
    new_assessments: list[VictoryAssessment] = []
    svc = VictoryService(dry_run=state.dry_run)

    # Query for pain points and explicit queries
    query_texts = []
    if changes.get("new_pain_points"):
        query_texts.extend(changes["new_pain_points"])
    if parsed.get("explicit_queries"):
        query_texts.extend(parsed["explicit_queries"])
    if not query_texts and not state.matched_victories:
        # First turn: broad query using company + industry
        query_texts.append(f"{state.company_name} {state.industry}")

    for query_text in query_texts:
        full_query = f"{state.industry} {query_text}"
        victories = svc.query_victories(full_query, k=3)
        for v in victories:
            vid = v.get("id", "")
            if vid and not _already_matched(state, vid):
                assessment = _assess_victory(v, state)
                if assessment:
                    new_assessments.append(assessment)
                    state.matched_victories.append(assessment)

    # Also query industry cases for ambitious tier
    if query_texts:
        combined = " ".join(query_texts)
        cases = svc.query_industry_cases(f"{state.industry} {combined}", k=2)
        for c in cases:
            cid = c.get("id", "")
            if cid and not _already_matched(state, cid):
                # Industry cases get AMBITIOUS tier by default
                ambitious = VictoryAssessment(
                    victory_id=cid,
                    victory_title=c.get("case_title", ""),
                    tier="AMBITIOUS",
                    confidence=0.45,
                    what_we_did=c.get("ai_application", {}).get("solution_description", "")
                    if isinstance(c.get("ai_application"), dict) else "",
                    problem_fit=f"Industry precedent in {c.get('industry', 'similar sector')}",
                    key_question="What is their appetite for transformative AI investment?",
                )
                new_assessments.append(ambitious)
                state.matched_victories.append(ambitious)

    # 5. If new tech was added, re-check prerequisites on existing matches
    if changes.get("new_tech"):
        for assessment in state.matched_victories:
            _update_prerequisites(assessment, state)

    # 6. Classify all matches into tiers
    state.recommendations = classify_recommendations(state.matched_victories)
    state.questions_pending = state.recommendations.top_questions

    # 7. Format response
    response = _format_response(state, changes, new_assessments)

    # 8. Record system turn
    state.turn_history.append(Turn(
        role="system", content=response,
        state_changes={"new_matches": len(new_assessments)},
    ))

    return response


def _update_prerequisites(assessment: VictoryAssessment, state: SessionState) -> None:
    """Move items from missing to confirmed if new tech matches."""
    tech_lower = {t.lower() for t in state.known_tech}
    still_missing = []
    for item in assessment.missing:
        matched = any(t in item.lower() for t in tech_lower)
        if matched:
            assessment.confirmed.append(f"{item} (analyst confirmed)")
            if assessment.confidence < 0.95:
                assessment.confidence = min(0.95, assessment.confidence + 0.05)
        else:
            still_missing.append(item)
    assessment.missing = still_missing


def _generate_pitch(state: SessionState) -> str:
    """Compile all assessments into a final pitch document."""
    if not state.recommendations:
        return "No victories matched yet. Tell me more about the company first."

    recs = state.recommendations
    sections = []
    sections.append(f"# AI Transformation Pitch: {state.company_name}\n")
    sections.append(f"Industry: {state.industry} | Size: {state.size_label}")
    if state.employee_count:
        sections.append(f"Employees: {state.employee_count}")
    sections.append("")

    if recs.easy_wins:
        sections.append("## Easy Wins (Delivered Solutions)")
        for w in recs.easy_wins:
            sections.append(f"\n### {w.victory_title} ({w.victory_id})")
            sections.append(f"Confidence: {w.confidence:.0%}")
            sections.append(w.what_we_did)
            sections.append(f"**Why this fits:** {w.problem_fit}")
            if w.calibration:
                sections.append(f"**Estimated value:** {w.calibration.estimated_value}")
                sections.append(f"**Basis:** {w.calibration.basis}")

    if recs.moderate_wins:
        sections.append("\n## Moderate Wins (Adaptations)")
        for w in recs.moderate_wins:
            sections.append(f"\n### {w.victory_title} ({w.victory_id})")
            sections.append(f"Confidence: {w.confidence:.0%}")
            sections.append(w.what_we_did)
            if w.adaptation_notes:
                sections.append(f"**Adaptation:** {w.adaptation_notes}")

    if recs.ambitious:
        sections.append("\n## Ambitious (Industry Precedent)")
        for w in recs.ambitious:
            sections.append(f"\n### {w.victory_title} ({w.victory_id})")
            sections.append(w.what_we_did)
            sections.append(f"**Why consider:** {w.problem_fit}")

    return "\n".join(sections)
