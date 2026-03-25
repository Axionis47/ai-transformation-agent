"""Tests for memory refactor: store wiring, promotion, provenance, contradiction."""
import pytest
from core import run_manager
from core.schemas import EvidenceItem, EvidenceSource, Opportunity, OpportunityTier
from services.memory.store import EvidenceStore, get_evidence_store
from services.memory.opp_store import get_opportunity_store
from services.memory.report_store import get_report_store
from services import trace


@pytest.fixture(autouse=True)
def clear_state():
    run_manager._runs.clear()
    get_evidence_store()._items.clear()
    get_opportunity_store()._items.clear()
    get_report_store()._items.clear()
    trace._events.clear()
    yield
    run_manager._runs.clear()
    get_evidence_store()._items.clear()
    get_opportunity_store()._items.clear()
    get_report_store()._items.clear()
    trace._events.clear()


def _ev(eid, run_id="r1", src=EvidenceSource.GOOGLE_SEARCH, rel=0.8,
        title="Test", snippet="test snippet", ref="ref"):
    return EvidenceItem(evidence_id=eid, run_id=run_id, source_type=src,
                        source_ref=ref, title=title, snippet=snippet,
                        relevance_score=rel)


def test_add_evidence_writes_to_store():
    run = run_manager.create_run("Acme", "logistics")
    run_manager.add_evidence(run.run_id, [_ev("e1", run_id=run.run_id)])
    stored = get_evidence_store().get_all(run.run_id)
    assert len(stored) == 1 and stored[0].evidence_id == "e1"


def test_store_opportunities_writes_to_store():
    run = run_manager.create_run("Acme", "logistics")
    opp = Opportunity(
        opportunity_id="opp-1", run_id=run.run_id, template_id="tmpl-1",
        name="Test Opp", description="desc", tier=OpportunityTier.EASY,
        feasibility=0.8, roi=0.7, time_to_value=0.6, confidence=0.9,
        evidence_ids=["e1"], assumptions={}, rationale="test",
    )
    run_manager.store_opportunities(run.run_id, [opp])
    stored = get_opportunity_store().get_all(run.run_id)
    assert len(stored) == 1 and stored[0].opportunity_id == "opp-1"


def test_store_report_writes_to_store():
    run = run_manager.create_run("Acme", "logistics")
    run_manager.store_report(run.run_id, {"title": "Test"})
    assert get_report_store().get(run.run_id) == {"title": "Test"}


def test_get_evidence_reads_from_store():
    run = run_manager.create_run("Acme", "logistics")
    run_manager.add_evidence(run.run_id, [_ev("e2", run_id=run.run_id)])
    assert any(e.evidence_id == "e2" for e in run_manager.get_evidence(run.run_id))


def test_dual_write_keeps_run_evidence():
    run = run_manager.create_run("Acme", "logistics")
    run_manager.add_evidence(run.run_id, [_ev("e3", run_id=run.run_id)])
    assert any(e.evidence_id == "e3" for e in run_manager.get_run(run.run_id).evidence)
