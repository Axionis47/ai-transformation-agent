"""Pitch synthesis engine — LLM-based opportunity evaluation.

Uses the model to evaluate template fit, tier, and scores.
"""
from __future__ import annotations

import uuid

from core.events import EventType
from core.schemas import (
    AssumptionsDraft,
    BudgetState,
    CompanyIntake,
    EvidenceItem,
    Opportunity,
    OpportunityTier,
    ReasoningState,
)
from engines.pitch import composer as composer_mod
from engines.pitch.matcher import match_templates, match_templates_llm
from engines.pitch.roi_model import translate_roi
from engines.pitch.scorer import score_opportunity
from engines.pitch.templates import get_templates
from engines.pitch.tier_classifier import classify_tier
from services.trace import emit

_MAX_OPPORTUNITIES = 5


class PitchEngine:
    def __init__(
        self,
        config: dict,
        engagement_lookup: dict[str, dict],
        grounder: object | None = None,
    ) -> None:
        self._config = config
        self._engagements = engagement_lookup
        self._templates = get_templates()
        self._grounder = grounder

    def synthesize(
        self,
        run_id: str,
        evidence: list[EvidenceItem],
        assumptions: AssumptionsDraft,
        company_intake: CompanyIntake,
        field_coverage: dict[str, float],
    ) -> list[Opportunity]:
        industry = company_intake.industry
        size_band = company_intake.employee_count_band
        evidence_map = {e.evidence_id: e for e in evidence}

        # Use LLM-based matching if grounder is available
        if self._grounder is not None:
            matches = match_templates_llm(
                evidence, self._templates, company_intake, assumptions,
                self._grounder, run_id, self._engagements,
            )
        else:
            matches = match_templates(evidence, self._templates)

        opportunities: list[Opportunity] = []

        for match in matches:
            tier, adaptation = classify_tier(match, industry, self._engagements)
            roi_estimate = translate_roi(
                match.matched_engagement_ids, size_band, industry, self._engagements,
            )
            scores = score_opportunity(match, roi_estimate, self._config, evidence_map)

            # Use LLM rationale if available, otherwise build from match data
            rationale = match.reasoning or (
                f"Score: {match.match_score:.2f}. "
                f"Backed by {len(match.matched_engagement_ids)} past engagements."
            )

            risks = match.risks or []
            if tier == OpportunityTier.HARD and not risks:
                risks.append("Low evidence coverage — high uncertainty in ROI projection.")

            opp = Opportunity(
                opportunity_id=str(uuid.uuid4()),
                run_id=run_id,
                template_id=match.template.template_id,
                name=match.template.name,
                description=match.template.description,
                tier=tier,
                feasibility=scores["feasibility"] or 0.0,
                roi=scores["roi"] or 0.0,
                time_to_value=scores["time_to_value"] or 0.0,
                confidence=scores["confidence"] or 0.0,
                evidence_ids=match.matched_evidence_ids,
                assumptions=roi_estimate.assumptions if roi_estimate else {},
                rationale=rationale,
                adaptation_needed=adaptation,
                risks=risks,
                data_sufficiency=scores.get("data_sufficiency", "scored"),
            )
            opportunities.append(opp)

        opportunities.sort(
            key=lambda o: (o.roi + o.feasibility + o.time_to_value + o.confidence),
            reverse=True,
        )
        opportunities = opportunities[:_MAX_OPPORTUNITIES]

        tier_counts = {t.value: sum(1 for o in opportunities if o.tier == t) for t in OpportunityTier}
        emit(run_id, EventType.OPPORTUNITIES_COMPUTED, {
            "total": len(opportunities), "tier_counts": tier_counts,
        })
        if any(o.assumptions for o in opportunities):
            emit(run_id, EventType.ROI_MODEL_COMPUTED, {
                "opportunities_with_roi": sum(1 for o in opportunities if o.assumptions),
            })
        emit(run_id, EventType.CONFIDENCE_COMPUTED, {
            "avg_confidence": round(
                sum(o.confidence for o in opportunities) / max(len(opportunities), 1), 3,
            ),
        })
        return opportunities

    def compose_report(
        self,
        run_id: str,
        opportunities: list[Opportunity],
        evidence: list[EvidenceItem],
        reasoning_state: ReasoningState,
        company_intake: CompanyIntake,
        budget_state: BudgetState,
    ) -> dict:
        report = composer_mod.compose_report(
            company_intake, opportunities, evidence, reasoning_state, budget_state,
        )
        emit(run_id, EventType.REPORT_RENDERED, {
            "opportunity_count": len(opportunities),
            "evidence_count": len(evidence),
        })
        return report
