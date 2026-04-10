"""Tests for services/rag/ingest.py — chunked ingestion pipeline."""

import tempfile

import pytest

from services.rag.ingest import (
    build_chunks,
    ensure_loaded,
    ingest,
    load_engagements,
)
from services.rag.schemas import ALL_CHUNK_TYPES, CHUNK_TYPE_COUNT, ChunkType, EngagementCase
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
        generalized_for="Any company with high-volume inbound requests.",
        lessons_learned=["Initial accuracy was low on long-tail categories."],
        discovery_insight="Real cost was rework from misrouting, not triage speed.",
        implementation_friction=["Zendesk webhook required IT security review."],
        baseline_metrics={"tickets_per_week": 1800},
    )


# --- load_engagements ---


def test_load_engagements_returns_list():
    engagements = load_engagements()
    assert isinstance(engagements, list)


def test_load_engagements_count_at_least_22():
    engagements = load_engagements()
    assert len(engagements) >= 22


def test_load_engagements_records_are_engagement_cases():
    engagements = load_engagements()
    for e in engagements:
        assert isinstance(e, EngagementCase)


# --- build_chunks ---


def test_build_chunks_returns_7_chunks(sample_engagement):
    chunks = build_chunks(sample_engagement)
    assert len(chunks) == CHUNK_TYPE_COUNT


def test_build_chunks_ids_follow_convention(sample_engagement):
    chunks = build_chunks(sample_engagement)
    for chunk in chunks:
        assert "::" in chunk["id"]
        eng_id, chunk_type = chunk["id"].split("::", 1)
        assert eng_id == "eng-test-001"
        assert chunk_type in [ct.value for ct in ALL_CHUNK_TYPES]


def test_build_chunks_all_types_present(sample_engagement):
    chunks = build_chunks(sample_engagement)
    types_found = {c["metadata"]["chunk_type"] for c in chunks}
    expected = {ct.value for ct in ALL_CHUNK_TYPES}
    assert types_found == expected


def test_build_chunks_metadata_has_all_fields(sample_engagement):
    chunks = build_chunks(sample_engagement)
    required_keys = {
        "engagement_id",
        "chunk_type",
        "title",
        "industry",
        "company_size_band",
        "workflow_area",
        "solution_shape",
    }
    for chunk in chunks:
        assert required_keys.issubset(chunk["metadata"].keys())


def test_build_chunks_metadata_values_correct(sample_engagement):
    chunks = build_chunks(sample_engagement)
    for chunk in chunks:
        assert chunk["metadata"]["engagement_id"] == "eng-test-001"
        assert chunk["metadata"]["title"] == "Test Support Automation"
        assert chunk["metadata"]["industry"] == "financial_services"
        assert chunk["metadata"]["solution_shape"] == "automation"


def test_build_chunks_text_is_nonempty(sample_engagement):
    chunks = build_chunks(sample_engagement)
    for chunk in chunks:
        assert len(chunk["text"]) > 20


def test_problem_pattern_contains_problem(sample_engagement):
    chunks = build_chunks(sample_engagement)
    pp = next(c for c in chunks if c["metadata"]["chunk_type"] == "problem_pattern")
    assert "manually classified" in pp["text"]
    assert "1800" in pp["text"]  # baseline metric


def test_solution_approach_contains_tech(sample_engagement):
    chunks = build_chunks(sample_engagement)
    sa = next(c for c in chunks if c["metadata"]["chunk_type"] == "solution_approach")
    assert "zendesk" in sa["text"]
    assert "8 weeks" in sa["text"]


def test_preconditions_contains_conditions_and_antipatterns(sample_engagement):
    chunks = build_chunks(sample_engagement)
    pc = next(c for c in chunks if c["metadata"]["chunk_type"] == "preconditions")
    assert "6 months of labelled data" in pc["text"]
    assert "under 200 tickets per week" in pc["text"]


def test_outcomes_contains_impact(sample_engagement):
    chunks = build_chunks(sample_engagement)
    oc = next(c for c in chunks if c["metadata"]["chunk_type"] == "outcomes")
    assert "time_saved_pct" in oc["text"]
    assert "ticket_volume" in oc["text"]


def test_discovery_insight_contains_insight(sample_engagement):
    chunks = build_chunks(sample_engagement)
    di = next(c for c in chunks if c["metadata"]["chunk_type"] == "discovery_insight")
    assert "rework from misrouting" in di["text"]


def test_implementation_friction_contains_friction(sample_engagement):
    chunks = build_chunks(sample_engagement)
    fr = next(c for c in chunks if c["metadata"]["chunk_type"] == "implementation_friction")
    assert "Zendesk webhook" in fr["text"]


def test_generalization_contains_cross_industry(sample_engagement):
    chunks = build_chunks(sample_engagement)
    gen = next(c for c in chunks if c["metadata"]["chunk_type"] == "generalization")
    assert "high-volume inbound requests" in gen["text"]


# --- ingest ---


def test_ingest_creates_7_chunks_per_engagement(store, sample_engagement):
    count = ingest(store, [sample_engagement])
    assert count == CHUNK_TYPE_COUNT
    assert store.count() == CHUNK_TYPE_COUNT


def test_ingest_all_engagements_correct_count(store):
    engagements = load_engagements()
    count = ingest(store, engagements)
    expected = len(engagements) * CHUNK_TYPE_COUNT
    assert count == expected
    assert store.count() == expected


# --- ensure_loaded ---


def test_ensure_loaded_ingests_all_chunks(store):
    count = ensure_loaded(store)
    assert count >= 22 * CHUNK_TYPE_COUNT


def test_ensure_loaded_is_idempotent(store):
    count_first = ensure_loaded(store)
    count_second = ensure_loaded(store)
    assert count_first == count_second
