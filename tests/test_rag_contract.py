"""RAG Contract success criteria tests.

These tests validate the contract defined in docs/RAG_CONTRACT.md.
Each test maps to a specific success criterion (SC-1 through SC-7).
If these pass, the RAG store is ready to hand off to the reasoning loop.
"""

import tempfile

import pytest

from services.rag.ingest import build_chunks, ensure_loaded, load_engagements
from services.rag.schemas import ALL_CHUNK_TYPES, CHUNK_TYPE_COUNT, ChunkType
from services.rag.store import RAGStore


@pytest.fixture(scope="module")
def loaded_store():
    """RAGStore seeded with all chunked engagements. Shared across module."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = RAGStore(persist_dir=tmpdir)
        ensure_loaded(store)
        yield store


@pytest.fixture(scope="module")
def engagements():
    return load_engagements()


# ===================================================================
# SC-1: Chunk completeness
# 22 engagements x 7 chunk types = 154 chunks. No duplicates.
# ===================================================================


class TestSC1ChunkCompleteness:
    def test_total_chunk_count(self, loaded_store, engagements):
        expected = len(engagements) * CHUNK_TYPE_COUNT
        assert loaded_store.count() == expected

    def test_every_engagement_has_7_chunks(self, engagements):
        for eng in engagements:
            chunks = build_chunks(eng)
            assert len(chunks) == CHUNK_TYPE_COUNT, (
                f"{eng.engagement_id} produced {len(chunks)} chunks, expected {CHUNK_TYPE_COUNT}"
            )

    def test_no_duplicate_ids(self, engagements):
        all_ids = []
        for eng in engagements:
            for chunk in build_chunks(eng):
                all_ids.append(chunk["id"])
        assert len(all_ids) == len(set(all_ids)), "Duplicate chunk IDs found"


# ===================================================================
# SC-2: Chunk isolation
# Different chunk types rank differently for different queries.
# ===================================================================


class TestSC2ChunkIsolation:
    def test_precondition_query_returns_precondition_chunks(self, loaded_store):
        """Query about prerequisites should rank preconditions chunks highest."""
        results = loaded_store.query("prerequisites conditions for success before starting", top_k=5)
        chunk_types = [r["metadata"]["chunk_type"] for r in results]
        assert "preconditions" in chunk_types, f"Expected preconditions in top 5, got: {chunk_types}"

    def test_problem_query_returns_problem_chunks(self, loaded_store):
        """Query about a specific problem should rank problem_pattern chunks high."""
        results = loaded_store.query("manual ticket triage high volume support team rework", top_k=5)
        chunk_types = [r["metadata"]["chunk_type"] for r in results]
        assert "problem_pattern" in chunk_types, f"Expected problem_pattern in top 5, got: {chunk_types}"

    def test_outcomes_query_returns_outcomes_chunks(self, loaded_store):
        """Query about ROI results should rank outcomes chunks high."""
        results = loaded_store.query("measured results ROI reduction savings improvement", top_k=5)
        chunk_types = [r["metadata"]["chunk_type"] for r in results]
        assert "outcomes" in chunk_types, f"Expected outcomes in top 5, got: {chunk_types}"

    def test_friction_query_returns_friction_chunks(self, loaded_store):
        """Query about what went wrong should rank friction chunks high."""
        results = loaded_store.query("implementation delays integration issues adoption resistance friction", top_k=5)
        chunk_types = [r["metadata"]["chunk_type"] for r in results]
        assert "implementation_friction" in chunk_types, (
            f"Expected implementation_friction in top 5, got: {chunk_types}"
        )

    def test_discovery_query_returns_discovery_chunks(self, loaded_store):
        """Query about surprises and pivots should rank discovery_insight high."""
        results = loaded_store.query("initial hypothesis was wrong real problem discovered pivot", top_k=5)
        chunk_types = [r["metadata"]["chunk_type"] for r in results]
        assert "discovery_insight" in chunk_types, f"Expected discovery_insight in top 5, got: {chunk_types}"


# ===================================================================
# SC-3: Cross-engagement retrieval
# Queries should return results from MULTIPLE engagements.
# ===================================================================


class TestSC3CrossEngagement:
    def test_broad_query_returns_multiple_engagements(self, loaded_store):
        """A generic problem query should match across engagements."""
        results = loaded_store.query("high volume manual processing automation", top_k=10)
        engagement_ids = {r["metadata"]["engagement_id"] for r in results}
        assert len(engagement_ids) >= 3, f"Expected >= 3 engagements, got {len(engagement_ids)}: {engagement_ids}"

    def test_cross_industry_pattern_returns_multiple_industries(self, loaded_store):
        """A cross-industry problem should return results from different industries."""
        results = loaded_store.query("high volume manual review queue false positives rework", top_k=10)
        industries = {r["metadata"]["industry"] for r in results}
        assert len(industries) >= 2, f"Expected >= 2 industries, got {len(industries)}: {industries}"

    def test_operations_query_spans_engagements(self, loaded_store):
        """Operations workflow query should find multiple operation engagements."""
        results = loaded_store.query("operations scheduling optimization fleet dispatch", top_k=10)
        engagement_ids = {r["metadata"]["engagement_id"] for r in results}
        assert len(engagement_ids) >= 2


# ===================================================================
# SC-4: Multi-hop coherence
# After finding one chunk, a follow-up query should find other facets
# of the same engagement.
# ===================================================================


class TestSC4MultiHop:
    def test_hop1_problem_to_hop2_preconditions(self, loaded_store):
        """Find a problem, then query for preconditions of same engagement."""
        # Hop 1: find dispatch optimization problem
        hop1 = loaded_store.query("logistics dispatch manual spreadsheets overtime drivers", top_k=3)
        assert len(hop1) > 0
        found_eng_id = hop1[0]["metadata"]["engagement_id"]
        found_title = hop1[0]["metadata"]["title"]

        # Hop 2: query for preconditions using terms from hop 1
        hop2 = loaded_store.query(f"prerequisites conditions {found_title}", top_k=5)
        hop2_eng_ids = {r["metadata"]["engagement_id"] for r in hop2}
        assert found_eng_id in hop2_eng_ids, f"Hop 2 should find {found_eng_id}, got: {hop2_eng_ids}"

    def test_hop1_problem_to_hop2_outcomes(self, loaded_store):
        """Find a problem, then query for outcomes of same engagement."""
        # Hop 1: find support triage problem
        hop1 = loaded_store.query("support team manually classified tickets triage rework", top_k=3)
        assert len(hop1) > 0
        found_eng_id = hop1[0]["metadata"]["engagement_id"]
        found_title = hop1[0]["metadata"]["title"]

        # Hop 2: query for results
        hop2 = loaded_store.query(f"measured results ROI {found_title}", top_k=5)
        hop2_eng_ids = {r["metadata"]["engagement_id"] for r in hop2}
        assert found_eng_id in hop2_eng_ids

    def test_hop1_generalization_to_hop2_friction(self, loaded_store):
        """Find a generalization, then query for implementation friction."""
        hop1 = loaded_store.query("appointment scheduling business high no-show rate", top_k=3)
        assert len(hop1) > 0
        found_eng_id = hop1[0]["metadata"]["engagement_id"]
        found_title = hop1[0]["metadata"]["title"]

        hop2 = loaded_store.query(f"implementation friction delays {found_title}", top_k=5)
        hop2_eng_ids = {r["metadata"]["engagement_id"] for r in hop2}
        assert found_eng_id in hop2_eng_ids

    def test_metadata_crossref_by_engagement_id(self, loaded_store):
        """Verify engagement_id in metadata enables exact cross-reference."""
        results = loaded_store.query("customer support triage", top_k=3)
        assert len(results) > 0
        target_id = results[0]["metadata"]["engagement_id"]

        # Now query broadly and filter by metadata
        all_results = loaded_store.query("automation support", top_k=20)
        same_eng = [r for r in all_results if r["metadata"]["engagement_id"] == target_id]
        if len(same_eng) > 1:
            # Multiple chunks from same engagement — should be different types
            types = {r["metadata"]["chunk_type"] for r in same_eng}
            assert len(types) == len(same_eng), "Same engagement returned duplicate chunk types"


# ===================================================================
# SC-5: Relevance scoring
# Top results should have meaningful scores; irrelevant should be low.
# ===================================================================


class TestSC5RelevanceScoring:
    def test_top_result_score_above_threshold(self, loaded_store):
        """A well-formed query should get top result >= 0.4."""
        result = loaded_store.query("customer support triage automation ticket classification", top_k=1)
        assert len(result) > 0
        assert result[0]["score"] >= 0.4, f"Top result score {result[0]['score']} below 0.4"

    def test_specific_query_scores_higher_than_vague(self, loaded_store):
        """A specific query should score higher than a vague one."""
        specific = loaded_store.query("logistics dispatch optimization route planning fleet drivers overtime", top_k=1)
        vague = loaded_store.query("business improvement", top_k=1)
        assert len(specific) > 0 and len(vague) > 0
        assert specific[0]["score"] >= vague[0]["score"]


# ===================================================================
# SC-6: Metadata integrity
# Every chunk has all required metadata fields populated correctly.
# ===================================================================


class TestSC6MetadataIntegrity:
    REQUIRED_METADATA_KEYS = {
        "engagement_id",
        "chunk_type",
        "title",
        "industry",
        "company_size_band",
        "workflow_area",
        "solution_shape",
    }

    VALID_INDUSTRIES = {
        "financial_services",
        "healthcare",
        "logistics",
        "retail",
        "manufacturing",
        "professional_services",
        "technology",
    }

    VALID_CHUNK_TYPES = {ct.value for ct in ALL_CHUNK_TYPES}

    VALID_SOLUTION_SHAPES = {"automation", "copilot", "decision_support"}

    def test_all_chunks_have_required_keys(self, engagements):
        for eng in engagements:
            for chunk in build_chunks(eng):
                missing = self.REQUIRED_METADATA_KEYS - set(chunk["metadata"].keys())
                assert not missing, f"{chunk['id']} missing metadata keys: {missing}"

    def test_all_chunk_types_are_valid(self, engagements):
        for eng in engagements:
            for chunk in build_chunks(eng):
                ct = chunk["metadata"]["chunk_type"]
                assert ct in self.VALID_CHUNK_TYPES, f"{chunk['id']} has invalid chunk_type: {ct}"

    def test_all_industries_are_valid(self, engagements):
        for eng in engagements:
            for chunk in build_chunks(eng):
                ind = chunk["metadata"]["industry"]
                assert ind in self.VALID_INDUSTRIES, f"{chunk['id']} has invalid industry: {ind}"

    def test_all_solution_shapes_are_valid(self, engagements):
        for eng in engagements:
            for chunk in build_chunks(eng):
                ss = chunk["metadata"]["solution_shape"]
                assert ss in self.VALID_SOLUTION_SHAPES, f"{chunk['id']} has invalid shape: {ss}"

    def test_engagement_id_matches_source(self, engagements):
        for eng in engagements:
            for chunk in build_chunks(eng):
                assert chunk["metadata"]["engagement_id"] == eng.engagement_id

    def test_chunk_id_format(self, engagements):
        """Every chunk ID must be {engagement_id}::{chunk_type}."""
        for eng in engagements:
            for chunk in build_chunks(eng):
                expected_id = f"{eng.engagement_id}::{chunk['metadata']['chunk_type']}"
                assert chunk["id"] == expected_id


# ===================================================================
# SC-7: Reasoning agent contract
# source_ref format enables multi-hop cross-referencing.
# ===================================================================


class TestSC7ReasoningAgentContract:
    def test_source_ref_contains_engagement_and_chunk_type(self, loaded_store):
        """Results from query should have parseable source_ref in the doc ID."""
        results = loaded_store.query("claims processing automation", top_k=5)
        for r in results:
            doc_id = r["id"]
            assert "::" in doc_id, f"Doc ID missing '::' separator: {doc_id}"
            eng_id, chunk_type = doc_id.split("::", 1)
            assert eng_id.startswith("eng-")
            assert chunk_type in {ct.value for ct in ALL_CHUNK_TYPES}

    def test_retrieval_meta_enables_followup_query(self, loaded_store):
        """After getting a result, its metadata has enough info for a follow-up."""
        results = loaded_store.query("fraud detection copilot analysts", top_k=3)
        assert len(results) > 0
        meta = results[0]["metadata"]
        # All fields needed for follow-up query are present
        assert meta["engagement_id"]
        assert meta["chunk_type"]
        assert meta["title"]
        assert meta["industry"]
