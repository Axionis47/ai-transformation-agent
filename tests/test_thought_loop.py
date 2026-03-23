"""Tests for engines/thought/reasoning_loop.py -- ThoughtEngine."""
from __future__ import annotations
import tempfile, uuid
from core.schemas import AssumptionsDraft, BudgetState, CompanyIntake, EvidenceItem, EvidenceSource
from engines.thought import ThoughtEngine
from services.grounder.fake_client import FakeGeminiClient
from services.grounder.grounder import Grounder
from services.rag.ingest import ensure_loaded
from services.rag.retrieval import RAGRetriever
from services.rag.store import RAGStore

INTAKE = CompanyIntake(company_name="Acme Logistics", industry="logistics")
NO_ASSUMPTIONS = AssumptionsDraft(assumptions=[], open_questions=[])
CFG = {
    "reasoning": {"depth_budget": 3, "confidence_threshold": 0.7},
    "budgets": {"external_search_query_budget": 5, "external_search_max_calls": 3,
        "rag_query_budget": 8, "rag_top_k": 5, "rag_min_score": 0.3},
    "confidence": {"evidence_coverage_weight": 0.45, "evidence_strength_weight": 0.35,
        "source_diversity_weight": 0.20},
}


def _engine(cfg=None, tmpdir="./data/chroma_store"):
    c = cfg or CFG
    client = FakeGeminiClient()
    store = RAGStore(persist_dir=tmpdir)
    ensure_loaded(store)
    eng = ThoughtEngine(Grounder(client, c), RAGRetriever(store, c), c)
    return eng, client


def test_loop_completes_depth_budget():
    with tempfile.TemporaryDirectory() as d:
        eng, _ = _engine(tmpdir=d)
        r = eng.run_loop("r1", INTAKE, NO_ASSUMPTIONS, BudgetState())
        assert r.completed is True and r.loops_run <= 3


def test_loop_stops_on_confidence_threshold():
    with tempfile.TemporaryDirectory() as d:
        cfg = {**CFG, "reasoning": {"depth_budget": 3, "confidence_threshold": 0.01}}
        eng, _ = _engine(cfg, d)
        r = eng.run_loop("r2", INTAKE, NO_ASSUMPTIONS, BudgetState())
        assert r.stop_reason == "confidence_met"


def test_loop_queries_grounder():
    with tempfile.TemporaryDirectory() as d:
        eng, client = _engine(tmpdir=d)
        eng.run_loop("r3", INTAKE, NO_ASSUMPTIONS, BudgetState())
        assert client.call_count >= 1


def test_loop_queries_rag():
    with tempfile.TemporaryDirectory() as d:
        eng, _ = _engine(tmpdir=d)
        r = eng.run_loop("r4", INTAKE, NO_ASSUMPTIONS, BudgetState())
        assert r.evidence_items is not None
