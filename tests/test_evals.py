"""Unit tests for evals rubrics, JudgeClient, and baseline runner."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
RUBRICS_DIR = REPO_ROOT / "evals" / "rubrics"
_RUBRIC_NAMES = ("tier_classification", "evidence_grounding", "roi_basis")


# ── Rubric YAML loading ────────────────────────────────────────────────────

class TestRubricYaml:
    @pytest.mark.parametrize("name", _RUBRIC_NAMES)
    def test_rubric_loads_without_error(self, name: str) -> None:
        path = RUBRICS_DIR / f"{name}.yaml"
        assert path.exists(), f"Rubric file missing: {path}"
        with open(path) as fh:
            data = yaml.safe_load(fh)
        assert data is not None

    @pytest.mark.parametrize("name", _RUBRIC_NAMES)
    def test_rubric_has_required_keys(self, name: str) -> None:
        with open(RUBRICS_DIR / f"{name}.yaml") as fh:
            data = yaml.safe_load(fh)
        assert "name" in data
        assert "version" in data
        assert "judge_prompt_template" in data

    @pytest.mark.parametrize("name", _RUBRIC_NAMES)
    def test_rubric_name_matches_filename(self, name: str) -> None:
        with open(RUBRICS_DIR / f"{name}.yaml") as fh:
            data = yaml.safe_load(fh)
        assert data["name"] == name


# ── JudgeClient ────────────────────────────────────────────────────────────

class TestJudgeClient:
    def test_no_api_key_sets_unavailable(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            import importlib
            import evals.judge_client as jc_mod
            importlib.reload(jc_mod)
            client = jc_mod.JudgeClient()
        assert client._available is False

    def test_score_returns_zero_without_api_key(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            from evals.judge_client import JudgeClient
            client = JudgeClient()
            rubric = str(RUBRICS_DIR / "tier_classification.yaml")
            result = client.score(rubric, {})
        assert result == 0.0

    def test_score_returns_float(self) -> None:
        from evals.judge_client import JudgeClient
        client = JudgeClient()
        rubric = str(RUBRICS_DIR / "evidence_grounding.yaml")
        result = client.score(rubric, {"title": "Test", "description": "x"})
        assert isinstance(result, float)

    def test_score_does_not_raise_on_bad_rubric(self) -> None:
        from evals.judge_client import JudgeClient
        client = JudgeClient()
        result = client.score("/nonexistent/rubric.yaml", {})
        assert result == 0.0


# ── ci_eval import ─────────────────────────────────────────────────────────

class TestCiEval:
    def test_ci_eval_imports_without_error(self) -> None:
        import evals.ci_eval  # noqa: F401 — just verifying importability


# ── test_companies.json ────────────────────────────────────────────────────

class TestTestCompanies:
    def test_file_loads_and_has_five_entries(self) -> None:
        path = REPO_ROOT / "evals" / "test_companies.json"
        assert path.exists()
        companies = json.loads(path.read_text())
        assert len(companies) == 5

    def test_each_entry_has_required_fields(self) -> None:
        path = REPO_ROOT / "evals" / "test_companies.json"
        companies = json.loads(path.read_text())
        for c in companies:
            assert "name" in c
            assert "url" in c
            assert "industry" in c
