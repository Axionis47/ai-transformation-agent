"""Tests for the eval harness: bundles, runner, and metrics."""
from __future__ import annotations

from evals.company_bundles import get_bundles
from evals.eval_runner import EvalResult
from evals.metrics import compute_metrics, format_report


# ---------------------------------------------------------------------------
# Bundle validation tests
# ---------------------------------------------------------------------------

def test_bundles_count():
    """get_bundles returns exactly 25 bundles."""
    bundles = get_bundles()
    assert len(bundles) == 25


def test_bundles_diverse_industries():
    """At least 6 unique industries are represented across the 25 bundles."""
    bundles = get_bundles()
    industries = {b.industry for b in bundles}
    assert len(industries) >= 6


def test_bundles_have_required_fields():
    """Every bundle has company_name, industry, employee_count_band, and notes as non-empty strings."""
    for bundle in get_bundles():
        assert isinstance(bundle.company_name, str) and bundle.company_name.strip()
        assert isinstance(bundle.industry, str) and bundle.industry.strip()
        assert isinstance(bundle.employee_count_band, str) and bundle.employee_count_band.strip()
        assert isinstance(bundle.notes, str) and bundle.notes.strip()


# ---------------------------------------------------------------------------
# Eval runner and metrics tests
# ---------------------------------------------------------------------------

def test_single_eval_run():
    """run_single on the first bundle produces a successful EvalResult with evidence_count > 0."""
    from evals.eval_runner import run_single
    bundle = get_bundles()[0]
    result = run_single(bundle)
    assert result.success is True, f"run_single failed: {result.error}"
    assert result.evidence_count > 0
    assert result.company_name == bundle.company_name
    assert result.industry == bundle.industry


def test_metrics_computation():
    """compute_metrics on a known list of EvalResults produces correct aggregates."""
    r1 = EvalResult(
        company_name="Alpha", industry="logistics", success=True, error=None,
        evidence_count=5, opportunity_count=3,
        tier_distribution={"easy": 1, "medium": 1, "hard": 1},
        field_coverage={"f1": 0.9, "f2": 0.7},
        overall_confidence=0.8, budget_adherence=True,
        rag_queries_used=3, search_queries_used=2,
        trace_event_count=10, latency_seconds=1.0,
    )
    r2 = EvalResult(
        company_name="Beta", industry="healthcare", success=True, error=None,
        evidence_count=3, opportunity_count=2,
        tier_distribution={"easy": 1, "medium": 0, "hard": 0},
        field_coverage={"f1": 0.5},
        overall_confidence=0.6, budget_adherence=True,
        rag_queries_used=2, search_queries_used=1,
        trace_event_count=8, latency_seconds=2.0,
    )
    r3 = EvalResult(
        company_name="Gamma", industry="retail", success=False, error="timeout",
        evidence_count=0, opportunity_count=0,
        tier_distribution={}, field_coverage={},
        overall_confidence=0.0, budget_adherence=True,
        rag_queries_used=0, search_queries_used=0,
        trace_event_count=0, latency_seconds=0.0,
    )
    m = compute_metrics([r1, r2, r3])
    assert m.total_runs == 3
    assert m.successful_runs == 2
    assert m.success_rate == round(2 / 3, 4)
    assert m.avg_evidence_count == 4.0
    assert m.avg_opportunity_count == 2.5
    assert m.avg_confidence == 0.7
    assert m.tier_totals["easy"] == 2
    assert m.budget_adherence_rate == 1.0


def test_eval_report_format():
    """format_report returns a string containing the header text."""
    r = EvalResult(
        company_name="TestCo", industry="manufacturing", success=True, error=None,
        evidence_count=4, opportunity_count=2,
        tier_distribution={"easy": 1, "medium": 1, "hard": 0},
        field_coverage={"f1": 0.8},
        overall_confidence=0.75, budget_adherence=True,
        rag_queries_used=3, search_queries_used=1,
        trace_event_count=12, latency_seconds=1.5,
    )
    m = compute_metrics([r])
    report = format_report(m)
    assert isinstance(report, str)
    assert "Eval Harness Report" in report
