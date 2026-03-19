"""Tests for rag/ingest_industry_case.py — CLI validation and ingestion."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag.ingest_industry_case import run, _validate, _generate_embed_text
from rag.schemas import IndustryCaseStudySchema

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_SAMPLE = _FIXTURES / "sample_industry_case.json"
_SEEDS = _FIXTURES / "rag_seeds" / "industry_cases.json"


def test_valid_sample_file_returns_exit_0(tmp_path):
    """Valid sample fixture validates and run() returns 0 (dry-run, no store write)."""
    code = run(str(_SAMPLE), dry_run=True)
    assert code == 0


def test_invalid_confidence_returns_exit_1(tmp_path):
    """A record with invalid confidence_in_data value exits with code 1."""
    bad = json.loads(_SAMPLE.read_text())
    bad["reported_outcomes"]["confidence_in_data"] = "very_high"
    bad_file = tmp_path / "bad_case.json"
    bad_file.write_text(json.dumps(bad))
    code = run(str(bad_file), dry_run=True)
    assert code == 1


def test_missing_file_returns_exit_1():
    """Non-existent file path exits with code 1."""
    code = run("/tmp/does_not_exist_abc123.json", dry_run=True)
    assert code == 1


def test_dry_run_does_not_call_chromadb(monkeypatch, tmp_path):
    """Dry-run mode must not import or call chromadb."""
    called = []

    def mock_import(name, *args, **kwargs):
        if name == "chromadb":
            called.append(name)
        return original_import(name, *args, **kwargs)

    import builtins
    original_import = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", mock_import)

    code = run(str(_SAMPLE), dry_run=True)
    assert code == 0
    assert "chromadb" not in called, "chromadb must not be imported in dry-run mode"


def test_five_seed_records_all_validate():
    """All 5 seed records in industry_cases.json pass IndustryCaseStudySchema validation."""
    records = json.loads(_SEEDS.read_text())
    assert len(records) == 5
    ids = set()
    for r in records:
        parsed = IndustryCaseStudySchema(**r)
        assert parsed.id.startswith("ind-")
        assert parsed.status == "active"
        assert parsed.industry != ""
        assert parsed.embed_text != ""
        ids.add(parsed.id)
    assert len(ids) == 5, "All 5 records must have unique IDs"


def test_seed_records_cover_five_industries():
    """Seeds cover logistics, healthcare, retail, financial_services, manufacturing."""
    records = json.loads(_SEEDS.read_text())
    industries = {r["industry"] for r in records}
    expected = {"logistics", "healthcare", "retail", "financial_services", "manufacturing"}
    assert industries == expected


def test_generate_embed_text_fills_missing():
    """_generate_embed_text produces non-empty text from case fields."""
    record = {
        "case_title": "Test Case",
        "industry": "retail",
        "ai_application": {"problem_addressed": "test problem", "solution_description": "test solution"},
        "reported_outcomes": {"headline_metric": "50% improvement"},
    }
    text = _generate_embed_text(record)
    assert "Test Case" in text
    assert "retail" in text
    assert "test problem" in text


def test_array_of_records_accepted(tmp_path):
    """CLI accepts a JSON array of records (not just a single object)."""
    single = json.loads(_SAMPLE.read_text())
    array_file = tmp_path / "array.json"
    array_file.write_text(json.dumps([single]))
    code = run(str(array_file), dry_run=True)
    assert code == 0


def test_validate_returns_errors_for_bad_record():
    """_validate() returns error list when confidence_in_data is invalid."""
    bad = {
        "id": "ind-bad",
        "case_title": "Bad Record",
        "industry": "retail",
        "reported_outcomes": {"confidence_in_data": "extremely_high"},
    }
    valid, errors = _validate([bad])
    assert len(valid) == 0
    assert len(errors) > 0
    assert "ind-bad" in errors[0]
