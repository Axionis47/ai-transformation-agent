"""Tests for engines/thought/mid.py -- MID gap detection."""
from __future__ import annotations
import uuid
from core.schemas import BudgetState, EvidenceItem, EvidenceSource
from engines.thought.mid import REQUIRED_FIELDS, assess_coverage, detect_gap

CONFIG = {
    "confidence": {"evidence_coverage_weight": 0.45, "evidence_strength_weight": 0.35, "source_diversity_weight": 0.20},
    "budgets": {"external_search_query_budget": 5, "external_search_max_calls": 3, "rag_query_budget": 8},
}


def _ev(s: str, src: EvidenceSource = EvidenceSource.GOOGLE_SEARCH) -> EvidenceItem:
    return EvidenceItem(evidence_id=str(uuid.uuid4()), run_id="r", source_type=src,
        source_ref=f"ref-{uuid.uuid4().hex[:8]}", title="T", snippet=s, relevance_score=0.8)


def _full():
    snippets = ["company provides offers", "company provides offers",
        "industry market sector", "industry market sector",
        "workflow process operations", "workflow process operations",
        "challenge problem bottleneck", "challenge problem bottleneck",
        "engagement automation roi reduction", "engagement automation roi reduction",
        "employees revenue customers volume", "employees revenue customers volume"]
    return [_ev(s) for s in snippets]


def test_empty_evidence_zero_coverage():
    cov, conf = assess_coverage([], CONFIG)
    assert all(cov[f] == 0.0 for f in REQUIRED_FIELDS) and conf == 0.0


def test_company_keywords_score_company_profile():
    cov, _ = assess_coverage([_ev("The company provides logistics services.")], CONFIG)
    assert cov["company_profile"] > 0.0


def test_industry_keywords_score_industry_context():
    cov, _ = assess_coverage([_ev("The industry faces market disruption in the sector.")], CONFIG)
    assert cov["industry_context"] > 0.0


def test_mid_returns_gap_for_lowest_coverage():
    gap = detect_gap([_ev("company provides products")], BudgetState(), CONFIG)
    assert gap is not None and gap.field in REQUIRED_FIELDS and gap.coverage < 0.5


def test_mid_returns_none_when_all_covered():
    assert detect_gap(_full(), BudgetState(), CONFIG) is None


def test_mid_suggests_ground_for_company_profile():
    gap = detect_gap([], BudgetState(), CONFIG)
    assert gap is not None and gap.action == "ground"


def test_mid_suggests_rag_for_similar_wins():
    ev = [_ev("company provides."), _ev("company provides."),
        _ev("industry market."), _ev("industry market."),
        _ev("workflow process."), _ev("workflow process."),
        _ev("challenge problem."), _ev("challenge problem."),
        _ev("employees revenue."), _ev("employees revenue.")]
    gap = detect_gap(ev, BudgetState(), CONFIG)
    assert gap is not None and gap.field == "similar_wins" and gap.action == "rag"


def test_mid_fallback_ask_user_when_budget_exhausted():
    state = BudgetState(external_search_queries_used=5)
    gap = detect_gap([], state, CONFIG)
    assert gap is not None and gap.action in ("ask_user", "rag")
