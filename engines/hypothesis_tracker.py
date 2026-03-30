"""Hypothesis lifecycle manager with causal reasoning chain.

Not just form/validate/reject — tracks WHY each hypothesis exists,
what evidence supports or contradicts it, and how it evolved.
The reasoning chain feeds directly into the report.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from core.schemas import (
    Hypothesis,
    HypothesisStatus,
    ReasoningStep,
    ReportOpportunity,
    TestResult,
)


class HypothesisTracker:
    """Manages hypothesis lifecycle with full reasoning chain."""

    def __init__(self) -> None:
        self._hypotheses: dict[str, Hypothesis] = {}

    def form(
        self,
        statement: str,
        category: str,
        target_process: str,
        evidence_for: list[str],
        reason: str,
        agent_id: str = "",
        parent_id: str | None = None,
    ) -> Hypothesis:
        """Form a new hypothesis. Records WHY it was formed."""
        hyp_id = f"hyp-{uuid.uuid4().hex[:8]}"
        h = Hypothesis(
            hypothesis_id=hyp_id,
            statement=statement,
            category=category,
            target_process=target_process,
            evidence_for=evidence_for,
            formed_by_agent=agent_id,
            parent_hypothesis_id=parent_id,
            status=HypothesisStatus.FORMING,
            confidence=0.5,  # hypotheses are formed from evidence — benefit of doubt
            reasoning_chain=[
                ReasoningStep(
                    step_type="formed_because",
                    description=reason,
                    evidence_ids=evidence_for,
                    confidence_delta=0.5,
                    timestamp=datetime.now(timezone.utc),
                ),
            ],
        )
        self._hypotheses[hyp_id] = h
        return h

    def record_test(
        self,
        hypothesis_id: str,
        test_result: TestResult,
        narrative: str,
    ) -> Hypothesis:
        """Record a test and its impact on confidence."""
        h = self._get(hypothesis_id)
        h.status = HypothesisStatus.TESTING
        h.test_results.append(test_result)
        h.confidence = max(0.0, min(1.0, h.confidence + test_result.impact_on_confidence))

        is_condition = (
            test_result.test_type
            in (
                "prerequisite",
                "condition",
                "caveat",
            )
            or "prerequisit" in narrative.lower()
            or "condition" in narrative.lower()
        )

        if test_result.impact_on_confidence < 0:
            h.evidence_against.extend(test_result.evidence_ids)
            step_type = "contradicted_by"
        elif is_condition:
            h.evidence_conditions.extend(test_result.evidence_ids)
            step_type = "tested_with"
        else:
            h.evidence_for.extend(test_result.evidence_ids)
            step_type = "tested_with"

        h.reasoning_chain.append(
            ReasoningStep(
                step_type=step_type,
                description=narrative,
                evidence_ids=test_result.evidence_ids,
                confidence_delta=test_result.impact_on_confidence,
                timestamp=datetime.now(timezone.utc),
            )
        )
        return h

    def revise(
        self,
        hypothesis_id: str,
        new_statement: str,
        reason: str,
        evidence_ids: list[str] | None = None,
    ) -> Hypothesis:
        """Revise a hypothesis — tracks evolution, not just pass/fail."""
        h = self._get(hypothesis_id)
        old_statement = h.statement
        h.statement = new_statement
        h.reasoning_chain.append(
            ReasoningStep(
                step_type="revised_because",
                description=f"Revised from '{old_statement}' — {reason}",
                evidence_ids=evidence_ids or [],
                confidence_delta=0.0,
                timestamp=datetime.now(timezone.utc),
            )
        )
        return h

    def validate(self, hypothesis_id: str, reason: str) -> Hypothesis:
        h = self._get(hypothesis_id)
        h.status = HypothesisStatus.VALIDATED
        h.reasoning_chain.append(
            ReasoningStep(
                step_type="validated_by",
                description=reason,
                evidence_ids=[],
                confidence_delta=0.0,
                timestamp=datetime.now(timezone.utc),
            )
        )
        return h

    def validate_with_conditions(
        self,
        hypothesis_id: str,
        reason: str,
        conditions: list[str],
    ) -> Hypothesis:
        """Validate a hypothesis conditionally — it passes, but with caveats."""
        h = self._get(hypothesis_id)
        h.status = HypothesisStatus.VALIDATED
        h.conditions_for_success = conditions
        h.reasoning_chain.append(
            ReasoningStep(
                step_type="validated_by",
                description=(f"Conditionally validated: {reason}. Requires: {', '.join(conditions)}"),
                evidence_ids=[],
                confidence_delta=0.0,
                timestamp=datetime.now(timezone.utc),
            )
        )
        return h

    def reject(self, hypothesis_id: str, reason: str) -> Hypothesis:
        h = self._get(hypothesis_id)
        h.status = HypothesisStatus.REJECTED
        h.confidence = 0.0
        h.reasoning_chain.append(
            ReasoningStep(
                step_type="contradicted_by",
                description=f"Rejected: {reason}",
                evidence_ids=[],
                confidence_delta=-h.confidence,
                timestamp=datetime.now(timezone.utc),
            )
        )
        return h

    def get(self, hypothesis_id: str) -> Hypothesis | None:
        return self._hypotheses.get(hypothesis_id)

    def get_all(self) -> list[Hypothesis]:
        return list(self._hypotheses.values())

    def get_by_status(self, status: HypothesisStatus) -> list[Hypothesis]:
        return [h for h in self._hypotheses.values() if h.status == status]

    def get_untested(self) -> list[Hypothesis]:
        return [h for h in self._hypotheses.values() if h.status == HypothesisStatus.FORMING]

    def get_low_confidence(self, threshold: float = 0.5) -> list[Hypothesis]:
        return [
            h for h in self._hypotheses.values() if h.status == HypothesisStatus.TESTING and h.confidence < threshold
        ]

    def should_investigate_more(self) -> bool:
        """True if there are untested or low-confidence hypotheses."""
        return bool(self.get_untested()) or bool(self.get_low_confidence())

    def get_reasoning_chain(self, hypothesis_id: str) -> list[ReasoningStep]:
        h = self._get(hypothesis_id)
        return list(h.reasoning_chain)

    def get_full_narrative(self, hypothesis_id: str) -> str:
        """Human-readable reasoning chain for reports."""
        h = self._get(hypothesis_id)
        parts = [f"Hypothesis: {h.statement}"]
        for step in h.reasoning_chain:
            prefix = {
                "formed_because": "Formed because",
                "tested_with": "Tested",
                "contradicted_by": "Contradicted by",
                "revised_because": "Revised",
                "validated_by": "Validated",
            }.get(step.step_type, step.step_type)
            delta = ""
            if step.confidence_delta != 0:
                sign = "+" if step.confidence_delta > 0 else ""
                delta = f" (confidence {sign}{step.confidence_delta:.0%})"
            parts.append(f"  → {prefix}: {step.description}{delta}")
        parts.append(f"  Final confidence: {h.confidence:.0%} — {h.status.value}")
        return "\n".join(parts)

    def to_opportunities(self) -> list[ReportOpportunity]:
        """Convert validated hypotheses into report opportunities."""
        validated = self.get_by_status(HypothesisStatus.VALIDATED)
        opps = []
        for h in sorted(validated, key=lambda x: x.confidence, reverse=True):
            opps.append(
                ReportOpportunity(
                    title=h.statement,
                    hypothesis_id=h.hypothesis_id,
                    narrative=self.get_full_narrative(h.hypothesis_id),
                    tier=self._classify_tier(h),
                    confidence=h.confidence,
                    risks=h.risks,
                    conditions_for_success=h.conditions_for_success,
                )
            )
        return opps

    @staticmethod
    def _classify_tier(h: Hypothesis) -> str:
        # Conditional validation means it is not a slam-dunk — at least medium
        has_conditions = bool(h.conditions_for_success)
        if not has_conditions and h.confidence >= 0.7 and len(h.analogous_engagements) >= 1:
            return "easy"
        if h.confidence >= 0.5 or has_conditions:
            return "medium"
        return "hard"

    def _get(self, hypothesis_id: str) -> Hypothesis:
        h = self._hypotheses.get(hypothesis_id)
        if h is None:
            raise ValueError(f"Hypothesis not found: {hypothesis_id}")
        return h
