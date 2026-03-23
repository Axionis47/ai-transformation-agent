from __future__ import annotations

import uuid
from pathlib import Path

from core.events import EventType
from core.schemas import (
    AssumptionsDraft,
    BudgetState,
    CompanyIntake,
    EvidenceItem,
    EvidenceSource,
    ReasoningLoopResult,
    ReasoningState,
    UserQuestion,
)
from engines.thought import assumptions as assumptions_mod
from engines.thought import mid
from engines.thought.evidence_acc import EvidenceAccumulator
from services.trace import emit

_PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts"

_USER_QUESTIONS: dict[str, str] = {
    "company_profile": "Can you describe what {company_name} does in your own words?",
    "business_processes": "What are the main workflows or processes at {company_name} that take the most time?",
    "pain_points": "What are the biggest operational challenges at {company_name} right now?",
    "scale_indicators": "Roughly how many employees does {company_name} have?",
    "similar_wins": "Can you describe a past AI or automation initiative at {company_name}?",
    "industry_context": "What major trends or disruptions are affecting the {industry} industry?",
}


def _load_prompt(name: str) -> str:
    path = _PROMPT_DIR / f"{name}.md"
    text = path.read_text()
    if text.startswith("---"):
        parts = text.split("---", 2)
        text = parts[2] if len(parts) > 2 else text
    return text.strip()


class ThoughtEngine:
    def __init__(self, grounder: object, rag_retriever: object, config: dict) -> None:
        reasoning = config.get("reasoning", {})
        self._depth_budget: int = int(reasoning.get("depth_budget", 3))
        self._threshold: float = float(reasoning.get("confidence_threshold", 0.7))
        self._grounder = grounder
        self._rag = rag_retriever
        self._config = config

    def generate_assumptions(
        self,
        run_id: str,
        intake: CompanyIntake,
        budget_state: BudgetState,
    ) -> AssumptionsDraft:
        notes_section = f"Notes: {intake.notes}" if intake.notes else ""
        template = _load_prompt("company_research")
        prompt = template.format(
            company_name=intake.company_name,
            industry=intake.industry,
            notes_section=notes_section,
        )
        result = self._grounder.ground(prompt, run_id, budget_state)  # type: ignore[attr-defined]
        if result.budget_exhausted:
            draft = AssumptionsDraft(
                assumptions=[],
                open_questions=["Company description", "Industry context", "Company size"],
            )
        else:
            draft = assumptions_mod.extract_assumptions(result.text, result.evidence_items)
        emit(run_id, EventType.ASSUMPTIONS_DRAFT_CREATED, {
            "fields_count": len(draft.assumptions),
            "open_questions_count": len(draft.open_questions),
        })
        return draft

    def run_loop(
        self,
        run_id: str,
        intake: CompanyIntake,
        assumptions: AssumptionsDraft,
        budget_state: BudgetState,
        existing_evidence: list[EvidenceItem] | None = None,
        start_loop: int = 0,
    ) -> ReasoningLoopResult:
        acc = EvidenceAccumulator(existing_evidence)
        stop_reason: str | None = None
        pending_question: UserQuestion | None = None

        for loop_idx in range(start_loop, self._depth_budget):
            emit(run_id, EventType.REASONING_LOOP_STARTED, {
                "loop": loop_idx,
                "depth_budget": self._depth_budget,
                "evidence_count": acc.count(),
            })
            coverage, confidence = mid.assess_coverage(acc.get_all(), self._config)
            if confidence >= self._threshold:
                stop_reason = "confidence_met"
                emit(run_id, EventType.REASONING_LOOP_COMPLETED, {
                    "loop": loop_idx, "action_taken": "stop_confidence", "new_evidence_count": 0,
                })
                break
            gap = mid.detect_gap(acc.get_all(), budget_state, self._config)
            if gap is None:
                stop_reason = "all_fields_covered"
                emit(run_id, EventType.REASONING_LOOP_COMPLETED, {
                    "loop": loop_idx, "action_taken": "stop_covered", "new_evidence_count": 0,
                })
                break
            emit(run_id, EventType.MID_GAP_DETECTED, {
                "field": gap.field, "coverage": gap.coverage, "action": gap.action,
            })
            new_count = 0
            if gap.action == "ground":
                query = self._build_grounding_query(gap.field, intake)
                result = self._grounder.ground(query, run_id, budget_state)  # type: ignore[attr-defined]
                if not result.budget_exhausted:
                    new_count = acc.add_many(result.evidence_items)
            elif gap.action == "rag":
                query = self._build_rag_query(gap.field, intake, assumptions)
                result = self._rag.query(query, run_id, budget_state)  # type: ignore[attr-defined]
                if not result.budget_exhausted:
                    new_count = acc.add_many(result.results)
            else:
                pending_question = self._build_user_question(gap.field, intake)
                emit(run_id, EventType.USER_QUESTION_ASKED, {
                    "question_id": pending_question.question_id,
                    "field": pending_question.field,
                    "question_text": pending_question.question_text,
                })
                coverage, confidence = mid.assess_coverage(acc.get_all(), self._config)
                return ReasoningLoopResult(
                    completed=False,
                    loops_run=loop_idx + 1,
                    evidence_items=acc.get_all(),
                    field_coverage=coverage,
                    overall_confidence=confidence,
                    pending_question=pending_question,
                    stop_reason=None,
                    coverage_gaps=[f for f, s in coverage.items() if s < 0.5],
                )
            emit(run_id, EventType.REASONING_LOOP_COMPLETED, {
                "loop": loop_idx, "action_taken": gap.action, "new_evidence_count": new_count,
            })
        if stop_reason is None:
            stop_reason = "depth_budget_exhausted"
        coverage, confidence = mid.assess_coverage(acc.get_all(), self._config)
        return ReasoningLoopResult(
            completed=True,
            loops_run=min(self._depth_budget - start_loop, self._depth_budget),
            evidence_items=acc.get_all(),
            field_coverage=coverage,
            overall_confidence=confidence,
            pending_question=None,
            stop_reason=stop_reason,
            coverage_gaps=[f for f, s in coverage.items() if s < 0.5],
        )

    def _build_grounding_query(self, gap_field: str, intake: CompanyIntake) -> str:
        templates = {
            "company_profile": "What does {company_name} do? Describe their core products, services, and market position.",
            "industry_context": "What are the major trends, challenges, and opportunities in the {industry} industry?",
            "business_processes": "What are the key business processes and operational workflows at {company_name}?",
            "pain_points": "What operational challenges do {industry} companies like {company_name} typically face?",
            "scale_indicators": "How large is {company_name}? Number of employees, revenue, customer base.",
        }
        template = templates.get(gap_field, "Tell me more about {company_name} in the {industry} industry.")
        return template.format(company_name=intake.company_name, industry=intake.industry)

    def _build_rag_query(
        self, gap_field: str, intake: CompanyIntake, assumptions: AssumptionsDraft
    ) -> str:
        pain_area = gap_field.replace("_", " ")
        band = intake.employee_count_band or "mid-market"
        return f"{intake.industry} {pain_area} automation implementation {band}"

    def _build_user_question(self, gap_field: str, intake: CompanyIntake) -> UserQuestion:
        template = _USER_QUESTIONS.get(gap_field, "Can you provide more details about {company_name}?")
        text = template.format(company_name=intake.company_name, industry=intake.industry)
        return UserQuestion(
            question_id=str(uuid.uuid4()),
            run_id="",
            field=gap_field,
            question_text=text,
            context=f"We need {gap_field.replace('_', ' ')} to match against similar past engagements.",
        )
