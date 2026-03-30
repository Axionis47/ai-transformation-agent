"""Context router: per-engine recall contracts with budgets and filtering.

Each engine gets a typed context assembly method that returns only what it needs,
under hard limits, with logging of what was dropped.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.events import EventType
from core.schemas import (
    AssumptionsDraft,
    BudgetState,
    CompanyIntake,
    EvidenceItem,
    Opportunity,
    ReasoningState,
)
from services.memory.pruning import (
    deduplicate_by_source,
    prune_by_relevance,
    prune_for_field_scope,
)
from services.trace import emit


@dataclass
class ThoughtContext:
    """Minimal context for the reasoning loop."""

    intake: CompanyIntake
    budget_state: BudgetState
    relevant_evidence: list[EvidenceItem]
    depth_budget: int
    confidence_threshold: float
    dropped_count: int = 0


@dataclass
class MIDContext:
    """Minimal context for MID assessment."""

    evidence: list[EvidenceItem]
    budget_state: BudgetState
    confidence_weights: dict[str, float]
    dropped_count: int = 0


@dataclass
class PitchContext:
    """Minimal context for pitch synthesis."""

    evidence: list[EvidenceItem]
    assumptions: AssumptionsDraft
    industry: str
    size_band: str | None
    field_coverage: dict[str, float]
    dropped_count: int = 0


@dataclass
class ReportContext:
    """Minimal context for report composition."""

    opportunities: list[Opportunity]
    linked_evidence: list[EvidenceItem]
    intake: CompanyIntake
    confidence: float
    coverage_gaps: list[str]
    budget_state: BudgetState
    dropped_count: int = 0


# --- Engine-specific budget defaults ---

THOUGHT_MAX_EVIDENCE = 15
THOUGHT_MIN_RELEVANCE = 0.3

MID_MAX_EVIDENCE = 20
MID_MIN_RELEVANCE = 0.0  # MID needs to see gaps, so low threshold

PITCH_MAX_EVIDENCE = 25
PITCH_MIN_RELEVANCE = 0.3

REPORT_MAX_EVIDENCE = 30  # only linked evidence, so naturally bounded


@dataclass
class RecallProfile:
    """Generic recall configuration for any agent or engine.

    Use this to define custom recall needs without adding a new method
    to ContextRouter for every new consumer.
    """

    name: str
    max_items: int = 15
    min_relevance: float = 0.3
    source_types: list[str] | None = None  # filter by source type
    field_scope: list[str] | None = None  # filter by field keywords
    max_per_field: int = 5  # only used if field_scope is set


class ContextRouter:
    """Assembles filtered, budgeted context for each engine."""

    def recall(
        self,
        run_id: str,
        evidence: list[EvidenceItem],
        profile: RecallProfile,
    ) -> tuple[list[EvidenceItem], int]:
        """Generic recall: filter evidence according to a RecallProfile.

        Returns (filtered_items, dropped_count). Any agent can use this
        by defining its own RecallProfile.
        """
        deduped = deduplicate_by_source(evidence)

        if profile.source_types:
            type_set = set(profile.source_types)
            deduped = [e for e in deduped if e.source_type.value in type_set]

        if profile.field_scope:
            from engines.thought.mid import _FIELD_SIGNALS

            deduped = prune_for_field_scope(deduped, _FIELD_SIGNALS, profile.field_scope, profile.max_per_field)

        pruned, dropped = prune_by_relevance(
            deduped,
            min_relevance=profile.min_relevance,
            max_items=profile.max_items,
        )

        self._log_recall(run_id, profile.name, len(evidence), len(pruned), dropped)
        return pruned, dropped

    def recall_for_thought(
        self,
        run_id: str,
        evidence: list[EvidenceItem],
        intake: CompanyIntake,
        budget_state: BudgetState,
        config: dict,
        unresolved_fields: list[str] | None = None,
    ) -> ThoughtContext:
        """Assemble context for the reasoning loop.

        Does NOT field-scope evidence. Thought loops need broad coverage
        to maintain overall confidence. Only deduplicates and relevance-prunes.
        """
        reasoning = config.get("reasoning", {})
        deduped = deduplicate_by_source(evidence)

        pruned, dropped = prune_by_relevance(
            deduped,
            min_relevance=THOUGHT_MIN_RELEVANCE,
            max_items=THOUGHT_MAX_EVIDENCE,
        )

        self._log_recall(run_id, "thought_loop", len(evidence), len(pruned), dropped)

        return ThoughtContext(
            intake=intake,
            budget_state=budget_state,
            relevant_evidence=pruned,
            depth_budget=int(reasoning.get("depth_budget", 3)),
            confidence_threshold=float(reasoning.get("confidence_threshold", 0.7)),
            dropped_count=dropped,
        )

    def recall_for_mid(
        self,
        run_id: str,
        evidence: list[EvidenceItem],
        budget_state: BudgetState,
        config: dict,
    ) -> MIDContext:
        """Assemble context for MID assessment."""
        deduped = deduplicate_by_source(evidence)
        pruned, dropped = prune_by_relevance(
            deduped,
            min_relevance=MID_MIN_RELEVANCE,
            max_items=MID_MAX_EVIDENCE,
        )
        conf_cfg = config.get("confidence", {})

        return MIDContext(
            evidence=pruned,
            budget_state=budget_state,
            confidence_weights={
                "evidence_coverage_weight": float(conf_cfg.get("evidence_coverage_weight", 0.45)),
                "evidence_strength_weight": float(conf_cfg.get("evidence_strength_weight", 0.35)),
                "source_diversity_weight": float(conf_cfg.get("source_diversity_weight", 0.20)),
            },
            dropped_count=dropped,
        )

    def recall_for_pitch(
        self,
        run_id: str,
        evidence: list[EvidenceItem],
        assumptions: AssumptionsDraft,
        intake: CompanyIntake,
        field_coverage: dict[str, float],
    ) -> PitchContext:
        """Assemble context for pitch synthesis."""
        deduped = deduplicate_by_source(evidence)
        pruned, dropped = prune_by_relevance(
            deduped,
            min_relevance=PITCH_MIN_RELEVANCE,
            max_items=PITCH_MAX_EVIDENCE,
        )

        self._log_recall(run_id, "pitch_synthesis", len(evidence), len(pruned), dropped)

        return PitchContext(
            evidence=pruned,
            assumptions=assumptions,
            industry=intake.industry,
            size_band=intake.employee_count_band,
            field_coverage=field_coverage,
            dropped_count=dropped,
        )

    def recall_for_report(
        self,
        run_id: str,
        opportunities: list[Opportunity],
        evidence: list[EvidenceItem],
        intake: CompanyIntake,
        reasoning_state: ReasoningState,
        budget_state: BudgetState,
    ) -> ReportContext:
        """Assemble context for report composition. Only linked evidence."""
        linked_ids: set[str] = set()
        for opp in opportunities:
            linked_ids.update(opp.evidence_ids)

        evidence_map = {e.evidence_id: e for e in evidence}
        linked = [evidence_map[eid] for eid in linked_ids if eid in evidence_map]
        dropped = len(evidence) - len(linked)

        self._log_recall(run_id, "report_composition", len(evidence), len(linked), dropped)

        return ReportContext(
            opportunities=opportunities,
            linked_evidence=linked,
            intake=intake,
            confidence=reasoning_state.overall_confidence,
            coverage_gaps=reasoning_state.coverage_gaps,
            budget_state=budget_state,
            dropped_count=dropped,
        )

    @staticmethod
    def _log_recall(run_id: str, need: str, total: int, returned: int, dropped: int) -> None:
        emit(
            run_id,
            EventType.QUERY_PLAN_CREATED,
            {
                "recall_need": need,
                "total_available": total,
                "returned": returned,
                "dropped": dropped,
            },
        )
