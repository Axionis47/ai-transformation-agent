from __future__ import annotations

from core.schemas import (
    AssumptionsDraft,
    BudgetState,
    CompanyIntake,
    EvidenceItem,
    Opportunity,
    ReasoningState,
)


def compose_report(
    company_intake: CompanyIntake,
    opportunities: list[Opportunity],
    evidence: list[EvidenceItem],
    reasoning_state: ReasoningState,
    budget_state: BudgetState,
    assumptions: AssumptionsDraft | None = None,
) -> dict:
    """Build operator brief, evidence annex, and metadata."""

    # Opportunities by tier with data_sufficiency
    by_tier: dict[str, list[dict]] = {"easy": [], "medium": [], "hard": []}
    all_evidence_ids: set[str] = set()
    for opp in opportunities:
        tier_key = opp.tier.value
        all_evidence_ids.update(opp.evidence_ids)
        by_tier.setdefault(tier_key, []).append(
            {
                "opportunity_id": opp.opportunity_id,
                "name": opp.name,
                "description": opp.description,
                "template_id": opp.template_id,
                "feasibility": opp.feasibility,
                "roi": opp.roi,
                "time_to_value": opp.time_to_value,
                "confidence": opp.confidence,
                "rationale": opp.rationale,
                "adaptation_needed": opp.adaptation_needed,
                "evidence_ids": opp.evidence_ids,
                "risks": opp.risks,
                "data_sufficiency": opp.data_sufficiency,
            }
        )

    # Evidence annex with opportunity cross-references
    evidence_annex = []
    for e in evidence:
        cited_by = [o.name for o in opportunities if e.evidence_id in o.evidence_ids]
        evidence_annex.append(
            {
                "evidence_id": e.evidence_id,
                "source_type": e.source_type.value,
                "title": e.title,
                "snippet": e.snippet[:300],
                "uri": e.uri,
                "relevance_score": e.relevance_score,
                "cited_by_opportunities": cited_by,
            }
        )

    # Assumptions snapshot
    assumptions_snapshot = []
    if assumptions:
        for a in assumptions.assumptions:
            assumptions_snapshot.append(
                {
                    "field": a.field,
                    "value": a.value,
                    "confidence": a.confidence,
                    "source": a.source,
                }
            )

    # Field coverage detail
    field_coverage = {}
    if reasoning_state and reasoning_state.field_coverage:
        field_coverage = reasoning_state.field_coverage

    overall_confidence = reasoning_state.overall_confidence if reasoning_state else 0.0
    coverage_gaps = reasoning_state.coverage_gaps if reasoning_state else []

    return {
        "operator_brief": {
            "company_name": company_intake.company_name,
            "industry": company_intake.industry,
            "employee_count_band": company_intake.employee_count_band,
            "notes": company_intake.notes,
            "analysis_confidence": round(overall_confidence, 3),
            "opportunities_by_tier": by_tier,
            "coverage_gaps": coverage_gaps,
            "field_coverage": field_coverage,
            "assumptions": assumptions_snapshot,
            "budget_usage": {
                "rag_queries_used": budget_state.rag_queries_used,
                "external_search_queries_used": budget_state.external_search_queries_used,
                "external_search_calls_used": budget_state.external_search_calls_used,
            },
        },
        "evidence_annex": evidence_annex,
        "metadata": {
            "total_evidence_items": len(evidence),
            "total_opportunities": len(opportunities),
            "reasoning_loops_completed": reasoning_state.loops_completed if reasoning_state else 0,
            "run_id": company_intake.company_name,
            "refinement_count": 0,
        },
    }
