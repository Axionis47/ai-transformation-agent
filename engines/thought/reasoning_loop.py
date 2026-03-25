"""ReAct-style reasoning loop.

Each iteration: THINK (LLM reasons about state) -> ACT (execute chosen tool) -> OBSERVE (accumulate results).
The LLM decides what to research and formulates specific queries. No keyword matching.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from core.events import EventType
from core.schemas import (
    AssumptionsDraft,
    BudgetState,
    CompanyIntake,
    EvidenceItem,
    ReasoningLoopResult,
    UserQuestion,
)
from core.json_parser import extract_json
from core.schemas import EvidenceSource
from engines.thought import assumptions as assumptions_mod
from engines.thought import mid
from engines.thought.evidence_acc import EvidenceAccumulator
from services.memory.pruning import prune_by_relevance
from services.trace import emit

_LOOP_MAX_EVIDENCE = 20
_LOOP_MIN_RELEVANCE = 0.2
_PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    path = _PROMPT_DIR / f"{name}.md"
    text = path.read_text()
    if text.startswith("---"):
        parts = text.split("---", 2)
        text = parts[2] if len(parts) > 2 else text
    return text.strip()


def _crossref_engagement(
    engagement: dict,
    company_summary: str,
    intake: CompanyIntake,
    grounder: object,
    run_id: str,
) -> dict:
    """Cross-reference a past engagement's conditions and anti-patterns against the company."""
    template = _load_prompt("case_crossref")
    conditions = engagement.get("conditions_for_success", [])
    anti_patterns = engagement.get("anti_patterns", [])

    prompt = template
    prompt = prompt.replace("{company_name}", intake.company_name)
    prompt = prompt.replace("{industry}", intake.industry)
    prompt = prompt.replace("{company_summary}", company_summary)
    prompt = prompt.replace("{eng_title}", engagement.get("title", ""))
    prompt = prompt.replace("{eng_industry}", engagement.get("industry", ""))
    prompt = prompt.replace("{eng_size}", engagement.get("company_size_band", ""))
    prompt = prompt.replace("{eng_problem}", engagement.get("problem", ""))
    prompt = prompt.replace("{eng_solution}", engagement.get("solution_shape", ""))
    prompt = prompt.replace("{eng_impact}", str(engagement.get("measured_impact", {})))
    prompt = prompt.replace("{discovery_insight}", engagement.get("discovery_insight", "Not available."))
    prompt = prompt.replace("{lessons_learned}", "\n".join(f"- {l}" for l in engagement.get("lessons_learned", [])) or "None")
    prompt = prompt.replace("{implementation_friction}", "\n".join(f"- {f}" for f in engagement.get("implementation_friction", [])) or "None")
    prompt = prompt.replace("{baseline_metrics}", str(engagement.get("baseline_metrics", {})))
    prompt = prompt.replace("{conditions_list}", "\n".join(f"- {c}" for c in conditions) or "None")
    prompt = prompt.replace("{anti_patterns_list}", "\n".join(f"- {a}" for a in anti_patterns) or "None")
    prompt = prompt.replace("{{", "{").replace("}}", "}")

    raw = grounder.reason(prompt, run_id)  # type: ignore[attr-defined]
    parsed = extract_json(raw)
    parsed["engagement_id"] = engagement.get("engagement_id", "")
    parsed["engagement_title"] = engagement.get("title", "")
    parsed["measured_impact"] = engagement.get("measured_impact", {})
    return parsed


class ThoughtEngine:
    def __init__(
        self,
        grounder: object,
        rag_retriever: object,
        config: dict,
        engagement_lookup: dict[str, dict] | None = None,
    ) -> None:
        reasoning = config.get("reasoning", {})
        self._depth_budget: int = int(reasoning.get("depth_budget", 3))
        self._threshold: float = float(reasoning.get("confidence_threshold", 0.7))
        self._grounder = grounder
        self._rag = rag_retriever
        self._config = config
        self._engagements = engagement_lookup or {}

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
            draft = assumptions_mod.extract_assumptions("", [])
        else:
            # Use LLM-based extraction
            draft = assumptions_mod.extract_assumptions_llm(
                result.text,
                result.evidence_items,
                self._grounder,
                run_id,
                intake.company_name,
                intake.industry,
            )
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
        reasoning_chain: list[str] = []
        confidence_history: list[float] = []
        all_contradictions: list[dict] = []

        # Pass budget_state through config so MID can read it
        config_with_budget = {**self._config, "_budget_state": budget_state}

        for loop_idx in range(start_loop, self._depth_budget):
            emit(run_id, EventType.REASONING_LOOP_STARTED, {
                "loop": loop_idx,
                "depth_budget": self._depth_budget,
                "evidence_count": acc.count(),
            })

            # THINK: LLM assesses state and decides next action (with prior reasoning)
            coverage, confidence, gap, loop_contradictions = mid.assess_coverage_with_llm(
                acc.get_all(),
                config_with_budget,
                self._grounder,
                run_id,
                intake,
                assumptions,
                prior_reasoning=reasoning_chain,
            )

            # Track confidence progression and contradictions
            confidence_history.append(confidence)
            if loop_contradictions:
                all_contradictions.extend(loop_contradictions)
                emit(run_id, EventType.CONTRADICTION_DETECTED, {
                    "loop": loop_idx, "count": len(loop_contradictions),
                })

            # Stagnation detection
            stag_n = int(reasoning.get("stagnation_threshold", 2))
            stag_delta = float(reasoning.get("stagnation_delta", 0.02))
            if len(confidence_history) >= stag_n:
                recent = confidence_history[-stag_n:]
                if max(recent) - min(recent) < stag_delta:
                    emit(run_id, EventType.CONFIDENCE_STAGNATION, {
                        "loop": loop_idx, "recent_values": recent,
                    })

            if confidence >= self._threshold:
                # Override: don't stop if critical fields are undercovered
                min_fc = float(reasoning.get("min_field_coverage", 0.3))
                critical_gaps = [f for f, s in coverage.items() if s < min_fc]
                if critical_gaps:
                    emit(run_id, EventType.MID_GAP_DETECTED, {
                        "override": "min_field_coverage",
                        "fields": critical_gaps,
                        "confidence": confidence,
                    })
                else:
                    stop_reason = "confidence_met"
                    emit(run_id, EventType.REASONING_LOOP_COMPLETED, {
                        "loop": loop_idx, "action_taken": "stop_confidence",
                        "new_evidence_count": 0,
                    })
                    break

            if gap is None:
                stop_reason = "all_fields_covered"
                emit(run_id, EventType.REASONING_LOOP_COMPLETED, {
                    "loop": loop_idx, "action_taken": "stop_llm_decided",
                    "new_evidence_count": 0,
                })
                break

            emit(run_id, EventType.MID_GAP_DETECTED, {
                "field": gap.field, "coverage": gap.coverage, "action": gap.action,
                "thinking": gap.thinking[:300],
                "query": gap.query[:200],
            })

            # ACT: Execute the LLM's chosen action with its formulated query
            new_count = 0
            if gap.action == "ground":
                # Use the LLM's specific query, not a template
                query = gap.query or f"Tell me about {intake.company_name} {gap.field}"
                result = self._grounder.ground(query, run_id, budget_state)  # type: ignore[attr-defined]
                if not result.budget_exhausted:
                    new_count = acc.add_many(result.evidence_items)
            elif gap.action == "rag":
                query = gap.query or f"{intake.industry} {gap.field} automation"
                result = self._rag.query(query, run_id, budget_state)  # type: ignore[attr-defined]
                if not result.budget_exhausted:
                    # Cross-reference WINS_KB engagements against the company
                    company_summary = "\n".join(
                        f"{a.field}: {a.value}" for a in assumptions.assumptions
                    ) if assumptions.assumptions else intake.company_name
                    for ev in result.results:
                        if ev.source_type == EvidenceSource.WINS_KB and ev.source_ref:
                            eng = self._engagements.get(ev.source_ref)
                            if eng:
                                crossref = _crossref_engagement(
                                    eng, company_summary, intake, self._grounder, run_id,
                                )
                                # Attach cross-reference to evidence metadata
                                ev.retrieval_meta["crossref"] = crossref
                                emit(run_id, EventType.RAG_RESULTS_FILTERED, {
                                    "engagement_id": ev.source_ref,
                                    "relevance": crossref.get("relevance", ""),
                                    "conditions_met": sum(
                                        1 for c in crossref.get("conditions_check", [])
                                        if c.get("status") == "MET"
                                    ),
                                    "anti_patterns_triggered": sum(
                                        1 for a in crossref.get("anti_pattern_check", [])
                                        if a.get("status") == "TRIGGERED"
                                    ),
                                })
                    new_count = acc.add_many(result.results)
            else:
                # ASK_USER: use the LLM's formulated question
                question_text = gap.query or f"Can you provide details about {gap.field.replace('_', ' ')}?"
                pending_question = UserQuestion(
                    question_id=str(uuid.uuid4()),
                    run_id=run_id,
                    field=gap.field,
                    question_text=question_text,
                    context=gap.thinking[:200] if gap.thinking else None,
                )
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

            # OBSERVE: Prune at loop boundary
            if acc.count() > _LOOP_MAX_EVIDENCE:
                pruned, _ = prune_by_relevance(
                    acc.get_all(), _LOOP_MIN_RELEVANCE, _LOOP_MAX_EVIDENCE,
                )
                acc = EvidenceAccumulator(pruned)

            # Record reasoning for next loop's context
            if gap.thinking:
                reasoning_chain.append(
                    f"Investigated {gap.field} via {gap.action}: {gap.thinking[:300]}"
                )

            emit(run_id, EventType.REASONING_LOOP_COMPLETED, {
                "loop": loop_idx, "action_taken": gap.action,
                "new_evidence_count": new_count,
                "evidence_after_prune": acc.count(),
                "thinking": gap.thinking[:200],
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
