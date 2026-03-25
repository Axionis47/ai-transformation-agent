"""Tests for engines/pitch/matcher.py -- template matching (fallback mode)."""
from __future__ import annotations

from core.schemas import EvidenceItem, EvidenceSource
from engines.pitch.matcher import match_templates, TemplateMatch
from engines.pitch.templates import get_templates


def _make_evidence(
    evidence_id: str,
    title: str,
    snippet: str,
    source_type: EvidenceSource = EvidenceSource.GOOGLE_SEARCH,
    source_ref: str = "",
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        run_id="run-test",
        source_type=source_type,
        source_ref=source_ref,
        title=title,
        snippet=snippet,
        relevance_score=0.8,
    )


SUPPORT_EVIDENCE = _make_evidence(
    "ev-001", "Support team ticket routing",
    "Customer support triage chatbot deflection help desk",
    EvidenceSource.WINS_KB, "eng-001",
)


def test_match_no_evidence():
    templates = get_templates()
    results = match_templates([], templates)
    assert results == []


def test_match_with_evidence_returns_results():
    templates = get_templates()
    results = match_templates([SUPPORT_EVIDENCE], templates)
    assert len(results) > 0


def test_match_score_ordering():
    templates = get_templates()
    ev = [SUPPORT_EVIDENCE, _make_evidence("ev-002", "Other", "Other data")]
    results = match_templates(ev, templates)
    scores = [m.match_score for m in results]
    assert scores == sorted(scores, reverse=True)


def test_match_limited_to_five():
    templates = get_templates()
    evidence = [_make_evidence(f"ev-{i}", f"Title {i}", f"Snippet {i}") for i in range(20)]
    results = match_templates(evidence, templates)
    assert len(results) <= 5


def test_match_tracks_engagement_ids():
    templates = get_templates()
    results = match_templates([SUPPORT_EVIDENCE], templates)
    all_eng_ids = []
    for m in results:
        all_eng_ids.extend(m.matched_engagement_ids)
    assert "eng-001" in all_eng_ids
