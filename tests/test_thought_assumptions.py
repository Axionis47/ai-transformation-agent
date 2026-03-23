"""Tests for engines/thought/assumptions.py -- extract_assumptions."""
from __future__ import annotations
from core.schemas import EvidenceItem, EvidenceSource
from engines.thought.assumptions import extract_assumptions
import uuid

SAMPLE_TEXT = (
    "Acme Logistics is a mid-market logistics company that provides freight forwarding. "
    "The logistics sector is experiencing rapid growth and market shifts. "
    "The company has approximately 500 employees and generates $50M revenue. "
    "They offer a warehouse management platform and cloud-based software. "
    "Their business model relies on subscription fees and per-shipment charges."
)

EMPTY_TEXT = ""


def _ev(score: float) -> EvidenceItem:
    return EvidenceItem(evidence_id=str(uuid.uuid4()), run_id="r",
        source_type=EvidenceSource.GOOGLE_SEARCH, source_ref=f"ref-{uuid.uuid4().hex[:6]}",
        title="T", snippet="s", relevance_score=score, confidence_score=score)


def test_assumptions_extracted_from_text():
    draft = extract_assumptions(SAMPLE_TEXT, [_ev(0.8)])
    assert len(draft.assumptions) > 0


def test_open_questions_for_missing_fields():
    # Text only covers some fields, expect open questions for uncovered ones
    minimal = "Acme is a company that provides services."
    draft = extract_assumptions(minimal, [])
    # Some fields will be open questions
    total = len(draft.assumptions) + len(draft.open_questions)
    assert total >= 6  # 6 ASSUMPTION_FIELDS total


def test_confidence_from_evidence():
    ev_items = [_ev(0.9), _ev(0.7)]
    draft = extract_assumptions(SAMPLE_TEXT, ev_items)
    for assumption in draft.assumptions:
        assert 0.0 < assumption.confidence <= 1.0


def test_empty_text_all_open_questions():
    draft = extract_assumptions(EMPTY_TEXT, [])
    assert len(draft.assumptions) == 0
    assert len(draft.open_questions) == 6


def test_source_is_grounding():
    draft = extract_assumptions(SAMPLE_TEXT, [])
    for assumption in draft.assumptions:
        assert assumption.source == "grounding"
