"""Tests for memory refactor: store wiring, promotion, provenance, contradiction."""
import pytest
from core import run_manager
from core.schemas import EvidenceItem, EvidenceSource, Opportunity, OpportunityTier
from services.memory.store import EvidenceStore, get_evidence_store
from services.memory.opp_store import get_opportunity_store
from services.memory.report_store import get_report_store
from services.storage.memory_store import MemoryStore
from services import trace


@pytest.fixture(autouse=True)
def clear_state():
    run_manager.init_storage(MemoryStore())
    get_evidence_store()._items.clear()
    get_opportunity_store()._items.clear()
    get_report_store()._items.clear()
    trace._events.clear()
    yield
    run_manager.init_storage(MemoryStore())
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

# --- Promotion, provenance, and contradiction tests ---
from core.schemas import Provenance
from services.memory.promotion import PromotionGate
from services.memory.contradiction import ContradictionDetector

def test_promotion_accepts_valid_evidence():
    result = PromotionGate(EvidenceStore()).promote_batch("r1", [_ev("e1")])
    assert result.accepted == 1 and result.rejected == 0

def test_promotion_rejects_below_threshold():
    result = PromotionGate(EvidenceStore(), min_relevance=0.5).promote_batch("r1", [_ev("e1", rel=0.3)])
    assert result.rejected == 1 and result.accepted == 0 and len(result.rejection_reasons) > 0

def test_promotion_deduplicates_by_source():
    store = EvidenceStore()
    store.add("r1", _ev("e1", rel=0.5))
    result = PromotionGate(store).promote_batch("r1", [_ev("e1", rel=0.8)])
    assert result.accepted == 1
    stored = store.get_all("r1")
    assert len(stored) == 1 and stored[0].relevance_score == 0.8

def test_promotion_emits_trace():
    PromotionGate(EvidenceStore()).promote_batch("r1", [_ev("e1", run_id="r1")])
    assert "EVIDENCE_PROMOTED" in [e.event_type for e in trace.get_events("r1")]

def test_promotion_records_rejection_reason():
    result = PromotionGate(EvidenceStore(), min_relevance=0.5).promote_batch("r1", [_ev("e1", rel=0.1)])
    assert any("relevance" in r for r in result.rejection_reasons)

def test_evidence_item_accepts_provenance():
    item = _ev("e1").model_copy(update={"provenance": Provenance(source_type="raw", confidence=0.8)})
    assert item.provenance is not None and item.provenance.confidence == 0.8

def test_evidence_item_provenance_optional():
    assert _ev("e1").provenance is None

def test_provenance_defaults():
    prov = Provenance()
    assert prov.source_evidence_ids == [] and prov.extraction_timestamp is None
    assert prov.source_type == "raw" and prov.confidence == 0.0

def test_user_vs_grounding_contradiction_detected():
    e = _ev("e1", src=EvidenceSource.GOOGLE_SEARCH, title="employees", snippet="5000 employees")
    n = _ev("e2", src=EvidenceSource.USER_PROVIDED, title="employees", snippet="200 employees")
    cs = ContradictionDetector().check([e], n)
    assert len(cs) == 1 and cs[0].resolution == "new_wins"

def test_user_correction_wins():
    e = _ev("e1", src=EvidenceSource.GOOGLE_SEARCH, title="employees", snippet="5000 employees")
    n = _ev("e2", src=EvidenceSource.USER_PROVIDED, title="employees", snippet="200 employees")
    assert ContradictionDetector().check([e], n)[0].resolution == "new_wins"

def test_same_source_no_contradiction():
    a = _ev("e1", src=EvidenceSource.WINS_KB, title="employees", snippet="5000 employees")
    b = _ev("e2", src=EvidenceSource.WINS_KB, title="employees", snippet="200 employees")
    assert ContradictionDetector().check([a], b) == []

def test_contradiction_emits_trace():
    store = get_evidence_store()
    store.add("r1", _ev("e1", run_id="r1", src=EvidenceSource.GOOGLE_SEARCH,
                         title="employees", snippet="5000 employees"))
    PromotionGate(store).promote_batch("r1", [_ev("e2", run_id="r1",
        src=EvidenceSource.USER_PROVIDED, title="employees", snippet="200 employees")])
    assert "EVIDENCE_CONTRADICTION" in [e.event_type for e in trace.get_events("r1")]
