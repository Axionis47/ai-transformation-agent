"""Tests for services/rag/ingest.py — ingestion pipeline and seed data."""
import tempfile

import pytest

from services.rag.ingest import (
    build_document_text,
    ensure_loaded,
    ingest,
    load_engagements,
)
from services.rag.schemas import EngagementCase
from services.rag.store import RAGStore


@pytest.fixture
def store():
    """Isolated RAGStore using a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield RAGStore(persist_dir=tmpdir)


@pytest.fixture
def sample_engagement() -> EngagementCase:
    return EngagementCase(
        engagement_id="eng-test-001",
        title="Test Support Automation",
        industry="financial_services",
        company_size_band="200-500",
        problem="Support team manually classified tickets.",
        workflow_area="support",
        solution_shape="automation",
        tech_stack=["zendesk"],
        timeline_weeks=8,
        measured_impact={"time_saved_pct": 40},
        roi_drivers=["ticket_volume"],
        conditions_for_success=["6 months of labelled data"],
        anti_patterns=["under 200 tickets per week"],
        tags=["support", "automation"],
    )


# --- load_engagements ---

def test_load_engagements_returns_list():
    engagements = load_engagements()
    assert isinstance(engagements, list)


def test_load_engagements_count_at_least_15():
    engagements = load_engagements()
    assert len(engagements) >= 15


def test_load_engagements_records_are_engagement_cases():
    engagements = load_engagements()
    for e in engagements:
        assert isinstance(e, EngagementCase)


def test_load_engagements_records_have_engagement_id():
    engagements = load_engagements()
    for e in engagements:
        assert e.engagement_id
        assert len(e.engagement_id) > 0


def test_load_engagements_records_have_title():
    engagements = load_engagements()
    for e in engagements:
        assert e.title
        assert len(e.title) > 0


def test_load_engagements_records_have_industry():
    engagements = load_engagements()
    for e in engagements:
        assert e.industry
        assert len(e.industry) > 0


def test_load_engagements_records_have_problem():
    engagements = load_engagements()
    for e in engagements:
        assert e.problem
        assert len(e.problem) > 0


def test_load_engagements_records_have_measured_impact():
    engagements = load_engagements()
    for e in engagements:
        assert isinstance(e.measured_impact, dict)
        assert len(e.measured_impact) > 0


# --- build_document_text ---

def test_build_document_text_includes_title(sample_engagement):
    text = build_document_text(sample_engagement)
    assert "Test Support Automation" in text


def test_build_document_text_includes_industry(sample_engagement):
    text = build_document_text(sample_engagement)
    assert "financial_services" in text


def test_build_document_text_includes_problem(sample_engagement):
    text = build_document_text(sample_engagement)
    assert "manually classified" in text


def test_build_document_text_includes_solution_shape(sample_engagement):
    text = build_document_text(sample_engagement)
    assert "automation" in text


def test_build_document_text_includes_impact(sample_engagement):
    text = build_document_text(sample_engagement)
    assert "time_saved_pct" in text


def test_build_document_text_returns_non_empty_string(sample_engagement):
    text = build_document_text(sample_engagement)
    assert isinstance(text, str)
    assert len(text) > 50


# --- ingest ---

def test_ingest_adds_documents_to_store(store, sample_engagement):
    count = ingest(store, [sample_engagement])
    assert count == 1
    assert store.count() == 1


def test_ingest_multiple_engagements(store):
    engagements = load_engagements()
    count = ingest(store, engagements)
    assert count == len(engagements)
    assert store.count() == len(engagements)


# --- ensure_loaded ---

def test_ensure_loaded_ingests_when_empty(store):
    count = ensure_loaded(store)
    assert count >= 15
    assert store.count() >= 15


def test_ensure_loaded_is_idempotent(store):
    count_first = ensure_loaded(store)
    count_second = ensure_loaded(store)
    assert count_first == count_second
    assert store.count() == count_first
