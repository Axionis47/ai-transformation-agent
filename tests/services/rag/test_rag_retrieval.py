"""Tests for services/rag/retrieval.py — RAGRetriever with budget enforcement."""

import tempfile

import pytest

from core.schemas import BudgetState, EvidenceSource
from services import trace as trace_module
from services.rag.ingest import ensure_loaded
from services.rag.retrieval import RAGQueryResult, RAGRetriever
from services.rag.store import RAGStore


def _config(rag_query_budget: int = 8, rag_top_k: int = 5, rag_min_score: float = 0.3) -> dict:
    return {
        "budgets": {
            "rag_query_budget": rag_query_budget,
            "rag_top_k": rag_top_k,
            "rag_min_score": rag_min_score,
        }
    }


@pytest.fixture
def loaded_store():
    """RAGStore seeded with all chunked engagements."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = RAGStore(persist_dir=tmpdir)
        ensure_loaded(store)
        yield store


@pytest.fixture(autouse=True)
def clear_trace_events():
    """Clear in-memory trace events before each test."""
    trace_module._events.clear()
    yield
    trace_module._events.clear()


# --- Basic query ---


def test_query_returns_rag_query_result(loaded_store):
    retriever = RAGRetriever(loaded_store, _config())
    result = retriever.query("customer support automation", "run-001", BudgetState())
    assert isinstance(result, RAGQueryResult)


def test_query_results_are_evidence_items(loaded_store):
    retriever = RAGRetriever(loaded_store, _config())
    result = retriever.query("customer support automation", "run-001", BudgetState())
    from core.schemas import EvidenceItem

    for item in result.results:
        assert isinstance(item, EvidenceItem)


def test_query_results_have_wins_kb_source_type(loaded_store):
    retriever = RAGRetriever(loaded_store, _config())
    result = retriever.query("customer support automation", "run-001", BudgetState())
    for item in result.results:
        assert item.source_type == EvidenceSource.WINS_KB


def test_query_results_have_evidence_id(loaded_store):
    retriever = RAGRetriever(loaded_store, _config())
    result = retriever.query("customer support automation", "run-001", BudgetState())
    for item in result.results:
        assert item.evidence_id
        assert len(item.evidence_id) > 0


def test_query_results_source_ref_is_chunked_id(loaded_store):
    """source_ref should be engagement_id::chunk_type format."""
    retriever = RAGRetriever(loaded_store, _config())
    result = retriever.query("customer support automation", "run-001", BudgetState())
    for item in result.results:
        assert "::" in item.source_ref, f"source_ref not chunked: {item.source_ref}"


def test_query_results_retrieval_meta_has_chunk_info(loaded_store):
    """retrieval_meta should include chunk_type and engagement_id."""
    retriever = RAGRetriever(loaded_store, _config())
    result = retriever.query("logistics dispatch", "run-001", BudgetState())
    for item in result.results:
        assert "chunk_type" in item.retrieval_meta
        assert "engagement_id" in item.retrieval_meta
        assert item.retrieval_meta["engagement_id"].startswith("eng-")


def test_query_results_have_relevance_score(loaded_store):
    retriever = RAGRetriever(loaded_store, _config())
    result = retriever.query("customer support automation", "run-001", BudgetState())
    for item in result.results:
        assert item.relevance_score is not None
        assert 0.0 <= item.relevance_score <= 1.0


def test_query_results_have_snippet(loaded_store):
    retriever = RAGRetriever(loaded_store, _config())
    result = retriever.query("customer support automation", "run-001", BudgetState())
    for item in result.results:
        assert item.snippet
        assert len(item.snippet) > 0


def test_query_snippet_truncated_to_500_chars(loaded_store):
    retriever = RAGRetriever(loaded_store, _config())
    result = retriever.query("customer support automation", "run-001", BudgetState())
    for item in result.results:
        assert len(item.snippet) <= 500


# --- Budget enforcement ---


def test_budget_increments_after_query(loaded_store):
    retriever = RAGRetriever(loaded_store, _config(rag_query_budget=5))
    budget = BudgetState()
    retriever.query("fraud detection", "run-002", budget)
    assert budget.rag_queries_used == 1


def test_budget_exhausted_returns_empty_results(loaded_store):
    retriever = RAGRetriever(loaded_store, _config(rag_query_budget=2))
    budget = BudgetState()
    retriever.query("query one", "run-003", budget)
    retriever.query("query two", "run-003", budget)
    result = retriever.query("query three — over budget", "run-003", budget)
    assert result.budget_exhausted is True
    assert result.results == []


def test_budget_exhausted_budget_state_not_incremented(loaded_store):
    retriever = RAGRetriever(loaded_store, _config(rag_query_budget=1))
    budget = BudgetState()
    retriever.query("first query", "run-004", budget)
    assert budget.rag_queries_used == 1
    retriever.query("second query — blocked", "run-004", budget)
    assert budget.rag_queries_used == 1  # not incremented on block


# --- Min score filtering ---


def test_min_score_very_high_returns_zero_results(loaded_store):
    retriever = RAGRetriever(loaded_store, _config(rag_min_score=0.99))
    result = retriever.query("customer support", "run-005", BudgetState())
    assert result.results == []


def test_min_score_zero_returns_results(loaded_store):
    retriever = RAGRetriever(loaded_store, _config(rag_min_score=0.0))
    result = retriever.query("customer support automation", "run-006", BudgetState())
    assert len(result.results) > 0


# --- Trace events ---


def test_trace_rag_query_executed_emitted(loaded_store):
    retriever = RAGRetriever(loaded_store, _config())
    retriever.query("patient scheduling", "run-008", BudgetState())
    events = trace_module.get_events("run-008")
    event_types = [e.event_type for e in events]
    assert "RAG_QUERY_EXECUTED" in event_types


def test_trace_rag_results_filtered_emitted(loaded_store):
    retriever = RAGRetriever(loaded_store, _config())
    retriever.query("patient scheduling", "run-009", BudgetState())
    events = trace_module.get_events("run-009")
    event_types = [e.event_type for e in events]
    assert "RAG_RESULTS_FILTERED" in event_types


def test_trace_budget_violation_emitted_when_exhausted(loaded_store):
    retriever = RAGRetriever(loaded_store, _config(rag_query_budget=1))
    budget = BudgetState()
    retriever.query("first query", "run-010", budget)
    retriever.query("blocked query", "run-010", budget)
    events = trace_module.get_events("run-010")
    event_types = [e.event_type for e in events]
    assert "BUDGET_VIOLATION_BLOCKED" in event_types
