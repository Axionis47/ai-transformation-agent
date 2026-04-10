"""Tests for engines/pitch/templates.py -- opportunity template definitions."""

from __future__ import annotations

import pytest

from engines.pitch.templates import OpportunityTemplate, get_templates

VALID_SHAPES = {"automation", "copilot", "decision_support"}
VALID_AREAS = {"support", "finance_ops", "operations", "rev_ops"}


@pytest.fixture(scope="module")
def templates():
    return get_templates()


def test_templates_load(templates):
    assert len(templates) > 0
    for t in templates:
        assert isinstance(t, OpportunityTemplate)
        assert t.template_id
        assert t.name
        assert t.description
        assert t.solution_shape
        assert t.workflow_area
        assert isinstance(t.win_signals, list)
        assert isinstance(t.anti_signals, list)
        assert isinstance(t.roi_drivers, list)
        assert isinstance(t.typical_timeline_weeks, int)
        assert isinstance(t.applicable_industries, list)
        assert isinstance(t.engagement_ids, list)


def test_templates_unique_ids(templates):
    ids = [t.template_id for t in templates]
    assert len(ids) == len(set(ids)), "Duplicate template_ids found"


def test_templates_cover_all_shapes(templates):
    shapes = {t.solution_shape for t in templates}
    assert "automation" in shapes
    assert "copilot" in shapes
    assert "decision_support" in shapes


def test_templates_have_signals(templates):
    for t in templates:
        assert len(t.win_signals) >= 2, f"Template {t.template_id} has fewer than 2 win_signals"


def test_templates_have_engagements(templates):
    for t in templates:
        assert len(t.engagement_ids) >= 1, f"Template {t.template_id} has no linked engagement_ids"


def test_templates_applicable_industries(templates):
    for t in templates:
        assert len(t.applicable_industries) >= 1, f"Template {t.template_id} has no applicable_industries"
