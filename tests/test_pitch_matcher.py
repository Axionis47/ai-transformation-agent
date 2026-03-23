"""Tests for engines/pitch/matcher.py -- template signal matching logic."""
from __future__ import annotations

import pytest
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
    "ev-001",
    "Support team ticket routing",
    "Customer support triage chatbot deflection help desk",
    EvidenceSource.WINS_KB,
    "eng-001",
)

COMPLIANCE_EVIDENCE = _make_evidence(
    "ev-002",
    "Regulatory compliance audit",
    "compliance regulatory audit policy governance review",
    EvidenceSource.GOOGLE_SEARCH,
)


def test_match_support_evidence():
    templates = get_templates()
    results = match_templates([SUPPORT_EVIDENCE], templates)
    ids = [m.template.template_id for m in results]
    assert "tpl-support-auto" in ids


def test_match_no_evidence():
    templates = get_templates()
    results = match_templates([], templates)
    assert results == []


def test_match_anti_signal_penalty():
    templates = get_templates()
    anti_ev = _make_evidence(
        "ev-anti",
        "No customer interaction",
        "b2b only no inbound requests support",
    )
    results_with = match_templates([anti_ev], templates)
    results_without = match_templates([SUPPORT_EVIDENCE], templates)
    support_with = next((m for m in results_with if m.template.template_id == "tpl-support-auto"), None)
    support_without = next((m for m in results_without if m.template.template_id == "tpl-support-auto"), None)
    if support_with and support_without:
        assert support_with.match_score <= support_without.match_score


def test_match_multiple_templates():
    templates = get_templates()
    rich_ev = _make_evidence(
        "ev-rich",
        "Support ticket routing compliance regulatory audit",
        "chatbot triage compliance audit policy review",
    )
    results = match_templates([rich_ev], templates)
    assert len(results) >= 2


def test_match_engagement_tracking():
    templates = get_templates()
    results = match_templates([SUPPORT_EVIDENCE], templates)
    support_match = next((m for m in results if m.template.template_id == "tpl-support-auto"), None)
    assert support_match is not None
    assert "eng-001" in support_match.matched_engagement_ids


def test_match_score_ordering():
    templates = get_templates()
    results = match_templates([SUPPORT_EVIDENCE, COMPLIANCE_EVIDENCE], templates)
    scores = [m.match_score for m in results]
    assert scores == sorted(scores, reverse=True)
