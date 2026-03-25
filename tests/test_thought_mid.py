"""Tests for engines/thought/mid.py -- LLM-based MID gap detection."""
from __future__ import annotations

import uuid

from core.schemas import BudgetState, EvidenceItem, EvidenceSource
from engines.thought.mid import REQUIRED_FIELDS, assess_coverage, _estimate_field_coverage

CONFIG = {
    "confidence": {"evidence_coverage_weight": 0.45, "evidence_strength_weight": 0.35, "source_diversity_weight": 0.20},
    "budgets": {"external_search_query_budget": 5, "external_search_max_calls": 3, "rag_query_budget": 8},
}


def _ev(s: str, src: EvidenceSource = EvidenceSource.GOOGLE_SEARCH, score: float = 0.8) -> EvidenceItem:
    return EvidenceItem(evidence_id=str(uuid.uuid4()), run_id="r", source_type=src,
        source_ref=f"ref-{uuid.uuid4().hex[:8]}", title="T", snippet=s, relevance_score=score)


def test_required_fields_defined():
    assert len(REQUIRED_FIELDS) == 6
    assert "company_profile" in REQUIRED_FIELDS
    assert "pain_points" in REQUIRED_FIELDS


def test_empty_evidence_zero_coverage():
    cov, conf = assess_coverage([], CONFIG)
    assert all(cov[f] == 0.0 for f in REQUIRED_FIELDS)
    assert conf == 0.0


def test_some_evidence_nonzero_coverage():
    evidence = [_ev("Company founded with revenue and employees"), _ev("Industry market sector analysis")]
    cov, conf = assess_coverage(evidence, CONFIG)
    assert conf > 0.0


def test_more_evidence_higher_coverage():
    few = [_ev("company founded in 2020")]
    many = [
        _ev("company founded in 2020 with 500 employees"),
        _ev("industry market trends and competitor analysis"),
        _ev("workflow automation and manual process bottleneck"),
        _ev("pain points and challenge with slow operations"),
        _ev("similar engagement case with deployment roi savings"),
        _ev("scale growth and transaction volume expansion"),
    ]
    _, conf_few = assess_coverage(few, CONFIG)
    _, conf_many = assess_coverage(many, CONFIG)
    assert conf_many > conf_few


def test_source_diversity_boosts_confidence():
    single = [_ev("A", EvidenceSource.GOOGLE_SEARCH), _ev("B", EvidenceSource.GOOGLE_SEARCH)]
    diverse = [_ev("A", EvidenceSource.GOOGLE_SEARCH), _ev("B", EvidenceSource.WINS_KB)]
    _, conf_single = assess_coverage(single, CONFIG)
    _, conf_diverse = assess_coverage(diverse, CONFIG)
    assert conf_diverse > conf_single


def test_estimate_field_coverage_empty():
    cov = _estimate_field_coverage([])
    assert all(v == 0.0 for v in cov.values())


def test_estimate_field_coverage_scales_with_count():
    few = _estimate_field_coverage([_ev("x")])
    many = _estimate_field_coverage([_ev("x") for _ in range(10)])
    assert all(many[f] >= few[f] for f in REQUIRED_FIELDS)


def test_confidence_weights_applied():
    evidence = [_ev("Test", score=0.9)]
    cov, conf = assess_coverage(evidence, CONFIG)
    assert 0.0 < conf < 1.0
