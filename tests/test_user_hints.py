"""Tests for UserHints schema validation."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from orchestrator.schemas import UserHints


def test_user_hints_valid_minimal():
    h = UserHints()
    assert h.pain_points == []
    assert h.known_tech == []
    assert h.industry == ""
    assert h.employee_count is None


def test_user_hints_valid_full():
    h = UserHints(
        pain_points=["we struggle with inventory forecasting accuracy"],
        known_tech=["Python", "AWS"],
        industry="logistics",
        employee_count=500,
        context="  B2B supply chain  ",
    )
    assert h.context == "B2B supply chain"
    assert len(h.pain_points) == 1
    assert h.industry == "logistics"


def test_user_hints_pain_point_too_short():
    with pytest.raises(ValidationError):
        UserHints(pain_points=["short"])


def test_user_hints_pain_point_too_long():
    with pytest.raises(ValidationError):
        UserHints(pain_points=["x" * 501])


def test_user_hints_known_tech_too_short():
    with pytest.raises(ValidationError):
        UserHints(known_tech=["x"])


def test_user_hints_known_tech_too_long():
    with pytest.raises(ValidationError):
        UserHints(known_tech=["x" * 51])


def test_user_hints_invalid_industry():
    with pytest.raises(ValidationError):
        UserHints(industry="martian_mining")


def test_user_hints_employee_count_out_of_range():
    with pytest.raises(ValidationError):
        UserHints(employee_count=0)
    with pytest.raises(ValidationError):
        UserHints(employee_count=1_000_001)


def test_user_hints_context_stripped():
    h = UserHints(context="  hello  ")
    assert h.context == "hello"
