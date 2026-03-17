"""Tests for orchestrator/gates.py — scraper content quality gate."""

from __future__ import annotations


from orchestrator.gates import scraper_quality_gate


def _make_company_data(about_text: str = "", postings: list | None = None) -> dict:
    return {
        "about_text": about_text,
        "job_postings": postings if postings is not None else [],
    }


def test_gate_passes_good_content():
    """200+ word about_text should pass the gate."""
    about = " ".join(["word"] * 200)
    passed, reason = scraper_quality_gate(_make_company_data(about_text=about))
    assert passed is True
    assert reason == ""


def test_gate_fails_empty():
    """Empty dict should fail immediately."""
    passed, reason = scraper_quality_gate({})
    assert passed is False
    assert "empty" in reason.lower()


def test_gate_fails_thin():
    """20-word about_text should fail the word count check."""
    about = " ".join(["word"] * 20)
    passed, reason = scraper_quality_gate(_make_company_data(about_text=about))
    assert passed is False
    assert "20 words" in reason


def test_gate_fails_error_page():
    """Content containing '404 not found' under 200 words should fail."""
    about = "404 not found " + " ".join(["word"] * 50)
    passed, reason = scraper_quality_gate(_make_company_data(about_text=about))
    assert passed is False
    assert "404 not found" in reason


def test_gate_passes_postings_only():
    """No about_text but enough words in job_postings should pass."""
    postings = [" ".join(["word"] * 60)]
    passed, reason = scraper_quality_gate(_make_company_data(postings=postings))
    assert passed is True
    assert reason == ""


def test_gate_fails_no_about_no_postings():
    """50+ words in product_text but no about_text and no postings should fail."""
    data = {"product_text": " ".join(["word"] * 60), "job_postings": []}
    passed, reason = scraper_quality_gate(data)
    assert passed is False
    assert "about page" in reason.lower()
