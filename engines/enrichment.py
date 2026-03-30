"""Enrichment engine — converts analyst input into evidence and identifies affected hypotheses.

Does NOT mutate run state. Returns a result the API endpoint uses
to drive re-testing and report regeneration.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from core.schemas import (
    EnrichmentInput,
    EvidenceItem,
    EvidenceSource,
    Hypothesis,
    Run,
)

_CATEGORY_TO_DIMENSION: dict[str, str] = {
    "technology": "technology",
    "financials": "revenue",
    "operations": "operations",
    "pain_points": "pain_point",
    "constraints": "operations",
    "corrections": "hypothesis_test",
    "additional_context": "operations",
}


@dataclass
class EnrichmentResult:
    evidence_items: list[EvidenceItem] = field(default_factory=list)
    affected_hypothesis_ids: set[str] = field(default_factory=set)
    pre_enrichment_confidence: dict[str, float] = field(default_factory=dict)
    pre_enrichment_status: dict[str, str] = field(default_factory=dict)


def prepare_enrichment(run: Run, inputs: list[EnrichmentInput]) -> EnrichmentResult:
    """Convert analyst inputs to evidence and identify affected hypotheses."""
    result = EnrichmentResult()

    for inp in inputs:
        ev = _input_to_evidence(run.run_id, inp)
        result.evidence_items.append(ev)

        # Collect explicitly targeted hypotheses
        for hid in inp.affected_hypothesis_ids:
            result.affected_hypothesis_ids.add(hid)

        # Auto-match by dimension/process overlap
        dim = _CATEGORY_TO_DIMENSION.get(inp.category.value, "operations")
        for h in run.hypotheses:
            if _hypothesis_matches(h, dim, inp):
                result.affected_hypothesis_ids.add(h.hypothesis_id)

    # If no specific matches, re-test all (new evidence could affect anything)
    if not result.affected_hypothesis_ids and run.hypotheses:
        result.affected_hypothesis_ids = {h.hypothesis_id for h in run.hypotheses}

    # Snapshot pre-enrichment state for diff
    for h in run.hypotheses:
        if h.hypothesis_id in result.affected_hypothesis_ids:
            result.pre_enrichment_confidence[h.hypothesis_id] = h.confidence
            result.pre_enrichment_status[h.hypothesis_id] = (
                h.status.value if hasattr(h.status, "value") else str(h.status)
            )

    return result


def _input_to_evidence(run_id: str, inp: EnrichmentInput) -> EvidenceItem:
    """Convert one EnrichmentInput to an EvidenceItem."""
    return EvidenceItem(
        evidence_id=f"ev-enrich-{uuid.uuid4().hex[:8]}",
        run_id=run_id,
        source_type=EvidenceSource.USER_PROVIDED,
        source_ref=f"analyst:{inp.category.value}",
        title=inp.title,
        snippet=inp.detail,
        relevance_score=inp.confidence,
        confidence_score=inp.confidence,
        produced_by="analyst_enrichment",
        dimension=_CATEGORY_TO_DIMENSION.get(inp.category.value, "operations"),
    )


def _hypothesis_matches(h: Hypothesis, dimension: str, inp: EnrichmentInput) -> bool:
    """Check if a hypothesis is affected by this enrichment input."""
    detail_lower = inp.detail.lower()
    # Corrections affect hypotheses that mention the same topic
    if inp.category.value == "corrections":
        return h.target_process.lower() in detail_lower or h.statement.lower()[:40] in detail_lower
    # Technology inputs affect tech-related hypotheses
    if dimension == "technology" and h.category in ("automation", "optimization"):
        return True
    # Process-area overlap
    if h.target_process.lower() in detail_lower:
        return True
    return False
