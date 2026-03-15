"""Tests for agents/rag_query.py — dry-run, query building, industry detection."""

from __future__ import annotations


def test_dry_run_returns_victory_records(monkeypatch):
    """Dry-run must return full victory records with win-NNN IDs."""
    monkeypatch.setenv("DRY_RUN", "true")

    from agents.rag_query import RAGQueryAgent

    agent = RAGQueryAgent()
    results = agent._run({})

    assert isinstance(results, list)
    assert len(results) >= 1
    for record in results:
        assert "id" in record
        assert record["id"].startswith("win-")
        assert "embed_text" in record
        assert "industry" in record


def test_build_query_logistics(monkeypatch):
    """A logistics company profile should produce a query containing 'Logistics'."""
    monkeypatch.delenv("DRY_RUN", raising=False)

    from agents.rag_query import RAGQueryAgent

    agent = RAGQueryAgent()
    company_data = {
        "about_text": "We are a regional carrier providing freight and trucking services across the US.",
        "job_postings": ["fleet manager", "dispatcher", "logistics coordinator"],
    }
    query = agent._build_query(company_data)

    assert "Logistics" in query
    assert "Looking for:" in query
    assert "Tenex delivery win" in query


def test_build_query_unknown_industry(monkeypatch):
    """Unknown industry falls back gracefully with a usable query."""
    monkeypatch.delenv("DRY_RUN", raising=False)

    from agents.rag_query import RAGQueryAgent

    agent = RAGQueryAgent()
    company_data = {
        "about_text": "A general purpose company with no recognisable sector keywords.",
        "job_postings": [],
    }
    query = agent._build_query(company_data)

    assert isinstance(query, str) and len(query) > 10
    assert "Looking for:" in query
    assert "Unknown" in query


def test_build_query_healthcare(monkeypatch):
    """A healthcare company profile should produce a query containing 'Healthcare'."""
    monkeypatch.delenv("DRY_RUN", raising=False)

    from agents.rag_query import RAGQueryAgent

    agent = RAGQueryAgent()
    company_data = {
        "about_text": "We operate a network of hospital clinics focused on patient care.",
        "job_postings": ["nurse practitioner", "clinical data analyst"],
    }
    query = agent._build_query(company_data)

    assert "Healthcare" in query


def test_build_query_empty_company_data(monkeypatch):
    """Empty company_data should not raise — returns a fallback query."""
    monkeypatch.delenv("DRY_RUN", raising=False)
    from agents.rag_query import RAGQueryAgent
    query = RAGQueryAgent()._build_query({})
    assert isinstance(query, str) and len(query) > 0
