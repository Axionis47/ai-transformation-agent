"""Tests for rag/ingest_solution.py — validation, dry-run, and ensure_seeds_loaded."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_SAMPLE = _FIXTURES / "sample_solution.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bad_solution(tmp_path: Path, overrides: dict) -> Path:
    """Write a modified sample_solution.json with overrides applied."""
    record = json.loads(_SAMPLE.read_text())
    record.update(overrides)
    p = tmp_path / "bad_solution.json"
    p.write_text(json.dumps(record))
    return p


# ---------------------------------------------------------------------------
# CLI validation tests
# ---------------------------------------------------------------------------

def test_valid_solution_dry_run_exits_zero(tmp_path, capsys):
    """A valid solution file should validate and exit 0 in dry-run mode."""
    from rag.ingest_solution import main

    with patch.object(sys, "argv", ["ingest_solution.py", "--file", str(_SAMPLE), "--dry-run"]):
        try:
            main()
        except SystemExit as exc:
            assert exc.code == 0 or exc.code is None

    captured = capsys.readouterr()
    assert "win-021" in captured.out
    assert "dry-run" in captured.out.lower()


def test_invalid_status_exits_one(tmp_path, capsys):
    """A solution with an invalid status enum value should exit code 1."""
    bad_path = _bad_solution(tmp_path, {"status": "unknown_status"})

    from rag.ingest_solution import main

    with patch.object(sys, "argv", ["ingest_solution.py", "--file", str(bad_path), "--dry-run"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1


def test_missing_required_field_exits_one(tmp_path, capsys):
    """A solution missing the required 'industry' field should exit code 1."""
    record = json.loads(_SAMPLE.read_text())
    del record["industry"]
    bad_path = tmp_path / "no_industry.json"
    bad_path.write_text(json.dumps(record))

    from rag.ingest_solution import main

    with patch.object(sys, "argv", ["ingest_solution.py", "--file", str(bad_path), "--dry-run"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1


def test_dry_run_does_not_write_to_store(tmp_path, capsys):
    """Dry-run mode must not call ChromaDB at all."""
    from rag.ingest_solution import main

    with patch("rag.vector_store.ChromaStore") as mock_store_cls:
        with patch.object(sys, "argv", ["ingest_solution.py", "--file", str(_SAMPLE), "--dry-run"]):
            try:
                main()
            except SystemExit:
                pass

    mock_store_cls.assert_not_called()


def test_valid_solution_array_dry_run(tmp_path, capsys):
    """An array with one valid record should work in dry-run mode."""
    record = json.loads(_SAMPLE.read_text())
    array_path = tmp_path / "array.json"
    array_path.write_text(json.dumps([record]))

    from rag.ingest_solution import main

    with patch.object(sys, "argv", ["ingest_solution.py", "--file", str(array_path), "--dry-run"]):
        try:
            main()
        except SystemExit as exc:
            assert exc.code == 0 or exc.code is None

    captured = capsys.readouterr()
    assert "win-021" in captured.out


# ---------------------------------------------------------------------------
# ensure_seeds_loaded — uses tenex_delivered collection
# ---------------------------------------------------------------------------

def test_ensure_seeds_loaded_uses_tenex_delivered(monkeypatch, tmp_path):
    """ensure_seeds_loaded must target the tenex_delivered collection, not ai_solutions."""
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path))
    monkeypatch.delenv("DRY_RUN", raising=False)

    from rag.ingest import ensure_seeds_loaded
    from rag.vector_store import ChromaStore

    ensure_seeds_loaded()

    store = ChromaStore(collection_name="tenex_delivered")
    store._init_chroma()
    assert store._collection.count() == 12

    # ai_solutions collection should NOT have been created
    import chromadb
    client = chromadb.PersistentClient(path=str(tmp_path))
    collections = [c.name for c in client.list_collections()]
    assert "ai_solutions" not in collections
