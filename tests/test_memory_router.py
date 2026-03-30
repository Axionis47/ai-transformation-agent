"""Tests for services/memory/router.py — context routing contracts.

These tests verify that:
1. Thought engine never receives all historical evidence by default
2. Pitch engine input excludes evidence below threshold
3. Report composer only sees selected opportunities and linked evidence
4. Recall obeys max_items and source filtering
5. System handles insufficient evidence cleanly
"""

import uuid

from core.schemas import (
    AssumptionsDraft,
    BudgetState,
    CompanyIntake,
    EvidenceItem,
    EvidenceSource,
    Opportunity,
    OpportunityTier,
    ReasoningState,
)
from services.memory.router import (
    PITCH_MAX_EVIDENCE,
    PITCH_MIN_RELEVANCE,
    THOUGHT_MAX_EVIDENCE,
    ContextRouter,
)


def _item(eid: str, score: float = 0.5, source: EvidenceSource = EvidenceSource.WINS_KB) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=eid,
        run_id="r1",
        source_type=source,
        source_ref=f"ref-{eid}",
        title=f"Title {eid}",
        snippet=f"Snippet {eid}",
        relevance_score=score,
    )


def _intake(industry: str = "logistics") -> CompanyIntake:
    return CompanyIntake(company_name="Test Co", industry=industry)


def _config() -> dict:
    return {
        "reasoning": {"depth_budget": 3, "confidence_threshold": 0.7},
        "confidence": {
            "evidence_coverage_weight": 0.45,
            "evidence_strength_weight": 0.35,
            "source_diversity_weight": 0.20,
        },
    }


def _opp(eid_list: list[str], tier: OpportunityTier = OpportunityTier.EASY) -> Opportunity:
    return Opportunity(
        opportunity_id=str(uuid.uuid4()),
        run_id="r1",
        template_id="tpl-1",
        name="Test Opp",
        description="Desc",
        tier=tier,
        feasibility=0.8,
        roi=0.7,
        time_to_value=0.9,
        confidence=0.6,
        evidence_ids=eid_list,
        assumptions={},
        rationale="test",
    )


# --- Thought Context Tests ---


def test_thought_context_respects_max_items():
    router = ContextRouter()
    evidence = [_item(f"e{i}", score=0.5 + i * 0.01) for i in range(30)]
    ctx = router.recall_for_thought("r1", evidence, _intake(), BudgetState(), _config())
    assert len(ctx.relevant_evidence) <= THOUGHT_MAX_EVIDENCE


def test_thought_context_filters_low_relevance():
    router = ContextRouter()
    evidence = [_item("e1", score=0.9), _item("e2", score=0.05)]
    ctx = router.recall_for_thought("r1", evidence, _intake(), BudgetState(), _config())
    scores = [e.relevance_score for e in ctx.relevant_evidence]
    assert all(s >= 0.3 for s in scores)


def test_thought_context_deduplicates():
    router = ContextRouter()
    e1 = _item("e1", score=0.5)
    e1.source_ref = "same-ref"
    e2 = _item("e2", score=0.9)
    e2.source_ref = "same-ref"
    ctx = router.recall_for_thought("r1", [e1, e2], _intake(), BudgetState(), _config())
    assert len(ctx.relevant_evidence) == 1
    assert ctx.relevant_evidence[0].relevance_score == 0.9


def test_thought_context_preserves_config():
    router = ContextRouter()
    ctx = router.recall_for_thought("r1", [], _intake(), BudgetState(), _config())
    assert ctx.depth_budget == 3
    assert ctx.confidence_threshold == 0.7


# --- Pitch Context Tests ---


def test_pitch_context_respects_max_items():
    router = ContextRouter()
    evidence = [_item(f"e{i}", score=0.5 + i * 0.005) for i in range(40)]
    intake = _intake()
    ctx = router.recall_for_pitch("r1", evidence, AssumptionsDraft(assumptions=[], open_questions=[]), intake, {})
    assert len(ctx.evidence) <= PITCH_MAX_EVIDENCE


def test_pitch_context_filters_low_relevance():
    router = ContextRouter()
    evidence = [_item("e1", score=0.9), _item("e2", score=0.1)]
    intake = _intake()
    ctx = router.recall_for_pitch("r1", evidence, AssumptionsDraft(assumptions=[], open_questions=[]), intake, {})
    assert len(ctx.evidence) == 1
    assert ctx.evidence[0].evidence_id == "e1"


def test_pitch_context_carries_metadata():
    router = ContextRouter()
    intake = _intake("healthcare")
    ctx = router.recall_for_pitch(
        "r1",
        [],
        AssumptionsDraft(assumptions=[], open_questions=[]),
        intake,
        {"field_a": 0.8},
    )
    assert ctx.industry == "healthcare"
    assert ctx.field_coverage == {"field_a": 0.8}


# --- Report Context Tests ---


def test_report_context_only_linked_evidence():
    """Report composer must only see evidence linked to selected opportunities."""
    router = ContextRouter()
    evidence = [_item("e1"), _item("e2"), _item("e3"), _item("e4")]
    opps = [_opp(["e1", "e3"])]
    state = ReasoningState(overall_confidence=0.7, coverage_gaps=["field_x"])
    ctx = router.recall_for_report("r1", opps, evidence, _intake(), state, BudgetState())
    linked_ids = {e.evidence_id for e in ctx.linked_evidence}
    assert linked_ids == {"e1", "e3"}
    assert ctx.dropped_count == 2


def test_report_context_handles_missing_evidence():
    """If opportunity references evidence_id not in evidence list, skip gracefully."""
    router = ContextRouter()
    evidence = [_item("e1")]
    opps = [_opp(["e1", "e999"])]
    state = ReasoningState(overall_confidence=0.5, coverage_gaps=[])
    ctx = router.recall_for_report("r1", opps, evidence, _intake(), state, BudgetState())
    assert len(ctx.linked_evidence) == 1


def test_report_context_carries_metadata():
    router = ContextRouter()
    state = ReasoningState(overall_confidence=0.85, coverage_gaps=["gap_a"])
    ctx = router.recall_for_report("r1", [], [], _intake(), state, BudgetState())
    assert ctx.confidence == 0.85
    assert ctx.coverage_gaps == ["gap_a"]


# --- Cross-cutting Tests ---


def test_empty_evidence_handled():
    router = ContextRouter()
    ctx = router.recall_for_thought("r1", [], _intake(), BudgetState(), _config())
    assert ctx.relevant_evidence == []
    assert ctx.dropped_count == 0


def test_no_engine_receives_full_blob():
    """Create a large evidence set and verify all engines return bounded results."""
    router = ContextRouter()
    evidence = [_item(f"e{i}", score=0.4 + (i % 10) * 0.05) for i in range(100)]
    intake = _intake()
    budget = BudgetState()
    config = _config()

    thought_ctx = router.recall_for_thought("r1", evidence, intake, budget, config)
    assert len(thought_ctx.relevant_evidence) <= THOUGHT_MAX_EVIDENCE

    pitch_ctx = router.recall_for_pitch(
        "r1",
        evidence,
        AssumptionsDraft(assumptions=[], open_questions=[]),
        intake,
        {},
    )
    assert len(pitch_ctx.evidence) <= PITCH_MAX_EVIDENCE

    opps = [_opp(["e1", "e5"])]
    state = ReasoningState(overall_confidence=0.5, coverage_gaps=[])
    report_ctx = router.recall_for_report("r1", opps, evidence, intake, state, budget)
    assert len(report_ctx.linked_evidence) <= 2  # only linked items
