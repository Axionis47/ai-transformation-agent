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
