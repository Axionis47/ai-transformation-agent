"""Tests for services/grounder/parser.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.grounder.parser import (
    ParsedGroundingMetadata,
    parse_grounding_response,
)

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "grounding_response.json"


@pytest.fixture
def raw_response() -> dict:
    with open(FIXTURE_PATH) as f:
        return json.load(f)


def test_parse_returns_correct_type(raw_response):
    result = parse_grounding_response(raw_response)
    assert isinstance(result, ParsedGroundingMetadata)


def test_parse_text_extracted(raw_response):
    result = parse_grounding_response(raw_response)
    assert "Acme Corp" in result.text


def test_parse_chunks_count(raw_response):
    result = parse_grounding_response(raw_response)
    assert len(result.chunks) == 3


def test_parse_search_queries(raw_response):
    result = parse_grounding_response(raw_response)
    assert result.search_query_count == 2
    assert result.search_query_count == len(result.search_queries)


def test_parse_supports_count(raw_response):
    result = parse_grounding_response(raw_response)
    assert len(result.supports) == 2


def test_parse_domain_extracted(raw_response):
    result = parse_grounding_response(raw_response)
    domains = [c.domain for c in result.chunks]
    assert "www.acmecorp.com" in domains
    assert "www.linkedin.com" in domains


def test_parse_confidence_scores_preserved(raw_response):
    result = parse_grounding_response(raw_response)
    first_support = result.supports[0]
    assert 0.92 in first_support.confidence_scores
    assert 0.85 in first_support.confidence_scores


def test_parse_entry_point_html(raw_response):
    result = parse_grounding_response(raw_response)
    assert result.search_entry_point_html is not None
    assert "search-entry" in result.search_entry_point_html


def test_parse_no_grounding_metadata():
    raw = {"text": "Some text", "grounding_metadata": None}
    result = parse_grounding_response(raw)
    assert result.text == "Some text"
    assert result.chunks == []
    assert result.supports == []
    assert result.search_query_count == 0
    assert result.search_queries == []


def test_parse_empty_search_queries(raw_response):
    raw_response["grounding_metadata"]["web_search_queries"] = []
    result = parse_grounding_response(raw_response)
    assert result.search_query_count == 0


def test_parse_missing_entry_point(raw_response):
    del raw_response["grounding_metadata"]["search_entry_point"]
    result = parse_grounding_response(raw_response)
    assert result.search_entry_point_html is None


def test_parse_malformed_chunk_skipped(raw_response):
    raw_response["grounding_metadata"]["grounding_chunks"].append({"web": {}})
    result = parse_grounding_response(raw_response)
    # chunk without uri should be skipped — original 3 remain
    assert len(result.chunks) == 3
