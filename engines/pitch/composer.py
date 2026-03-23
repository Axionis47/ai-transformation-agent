from __future__ import annotations

from core.schemas import (
    BudgetState,
    CompanyIntake,
    EvidenceItem,
    Opportunity,
    OpportunityTier,
    ReasoningState,
)


def compose_report(
    company_intake: CompanyIntake,
    opportunities: list[Opportunity],
    evidence: list[EvidenceItem],
    reasoning_state: ReasoningState,
    budget_state: BudgetState,
) -> dict:
    """Build the operator brief, evidence annex, and metadata report dict."""
    by_tier: dict[str, list[dict]] = {"easy": [], "medium": [], "hard": []}
    for opp in opportunities:
        tier_key = opp.tier.value
        by_tier.setdefault(tier_key, []).append({
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
        })

    evidence_annex = [
        {
            "evidence_id": e.evidence_id,
            "source_type": e.source_type.value,
            "title": e.title,
            "snippet": e.snippet[:200],
            "uri": e.uri,
        }
        for e in evidence
    ]

    budget_usage = {
        "rag_queries_used": budget_state.rag_queries_used,
        "external_search_queries_used": budget_state.external_search_queries_used,
        "external_search_calls_used": budget_state.external_search_calls_used,
    }

    overall_confidence = reasoning_state.overall_confidence if reasoning_state else 0.0
    coverage_gaps = reasoning_state.coverage_gaps if reasoning_state else []

    return {
        "operator_brief": {
            "company_name": company_intake.company_name,
            "industry": company_intake.industry,
            "analysis_confidence": round(overall_confidence, 3),
            "opportunities_by_tier": by_tier,
            "coverage_gaps": coverage_gaps,
            "budget_usage": budget_usage,
        },
        "evidence_annex": evidence_annex,
        "metadata": {
            "total_evidence_items": len(evidence),
            "total_opportunities": len(opportunities),
            "reasoning_loops_completed": reasoning_state.loops_completed if reasoning_state else 0,
            "run_id": company_intake.company_name,
        },
    }
