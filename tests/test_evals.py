"""Unit tests for evals rubrics, JudgeClient, and baseline runner."""

from __future__ import annotations

import json
from pathlib import Path

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
    def test_judge_client_initializes(self) -> None:
        from evals.judge_client import JudgeClient
        client = JudgeClient()
        # Should initialize (may or may not be available depending on GCP auth)
        assert isinstance(client._available, bool)

    def test_score_returns_float_or_zero(self) -> None:
        from evals.judge_client import JudgeClient
        client = JudgeClient()
        rubric = str(RUBRICS_DIR / "tier_classification.yaml")
        result = client.score(rubric, {})
        assert isinstance(result, float)

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


# ── sprint_6 baseline verification ─────────────────────────────────────────

class TestSprint6Baseline:
    def _load(self) -> dict:
        path = REPO_ROOT / "evals" / "baselines.json"
        assert path.exists(), "baselines.json not found"
        return json.loads(path.read_text())

    def test_sprint_6_key_exists(self) -> None:
        data = self._load()
        assert "sprint_6" in data, "sprint_6 key missing from baselines.json"

    def test_sprint_6_has_companies_dict(self) -> None:
        data = self._load()
        entry = data["sprint_6"]
        assert "companies" in entry, "sprint_6 missing companies dict"
        assert isinstance(entry["companies"], dict)
        assert len(entry["companies"]) > 0

    def test_sprint_6_has_averages_dict(self) -> None:
        data = self._load()
        entry = data["sprint_6"]
        assert "averages" in entry, "sprint_6 missing averages dict"
        averages = entry["averages"]
        for key in ("tier_classification", "evidence_grounding", "roi_basis"):
            assert key in averages, f"averages missing key: {key}"

    def test_sprint_6_has_run_date(self) -> None:
        data = self._load()
        assert "run_date" in data["sprint_6"]

    def test_sprint_6_has_run_date_format(self) -> None:
        data = self._load()
        run_date = data["sprint_6"]["run_date"]
        assert len(run_date) == 10, "run_date should be YYYY-MM-DD format"

    def test_sprint_6_company_scores_are_floats(self) -> None:
        data = self._load()
        for company, scores in data["sprint_6"]["companies"].items():
            for rubric, score in scores.items():
                assert isinstance(score, float), (
                    f"{company}/{rubric} score is not a float: {score!r}"
                )


# ── ci_eval _SPRINT constant ────────────────────────────────────────────────

class TestCiEvalSprint:
    def test_sprint_constant_is_sprint_8(self) -> None:
        import importlib
        import evals.ci_eval as ci_mod
        importlib.reload(ci_mod)
        assert ci_mod._SPRINT == "sprint_8", (
            f"_SPRINT should be 'sprint_8', got {ci_mod._SPRINT!r}"
        )


# ── ci_eval _RUBRICS has 11 keys ─────────────────────────────────────────────

class TestCiEvalRubrics:
    def test_rubrics_dict_has_eleven_keys(self) -> None:
        import importlib
        import evals.ci_eval as ci_mod
        importlib.reload(ci_mod)
        assert len(ci_mod._RUBRICS) == 11, (
            f"_RUBRICS should have 11 keys, got {len(ci_mod._RUBRICS)}: {list(ci_mod._RUBRICS)}"
        )

    def test_rubrics_dict_has_all_expected_keys(self) -> None:
        import importlib
        import evals.ci_eval as ci_mod
        importlib.reload(ci_mod)
        expected = (
            "tier_classification", "evidence_grounding", "roi_basis",
            "match_quality_delivered", "match_quality_adaptation", "match_quality_ambitious",
            "report_exec_summary", "report_current_state", "report_use_cases",
            "report_roadmap", "report_roi_analysis",
        )
        for key in expected:
            assert key in ci_mod._RUBRICS, f"_RUBRICS missing key: {key}"


# ── ci_eval _match_vars extracts correct fields ──────────────────────────────

class TestMatchVars:
    def test_match_vars_extracts_base_fields(self) -> None:
        from evals.ci_eval import _match_vars
        sample_match = {
            "match_tier": "DELIVERED",
            "source_id": "win-001",
            "source_title": "Route Optimization",
            "source_industry": "logistics",
            "confidence": 0.85,
            "relevance_note": "Direct match on fleet management signals",
            "adaptation_notes": "",
            "gap_from_base": 0.0,
            "industry_examples": [],
            "source_citations": [],
        }
        sample_signals = {"industry": "logistics", "scale": "mid-market", "composite_score": 2.5}
        result = _match_vars(sample_match, sample_signals)
        assert result["match_tier"] == "DELIVERED"
        assert result["source_id"] == "win-001"
        assert result["confidence"] == 0.85
        assert result["company_industry"] == "logistics"
        assert result["company_scale"] == "mid-market"
        assert result["composite_score"] == 2.5

    def test_match_vars_adaptation_fields(self) -> None:
        from evals.ci_eval import _match_vars
        match = {
            "match_tier": "ADAPTATION", "source_id": "win-003",
            "source_title": "Demand Forecasting", "source_industry": "retail",
            "confidence": 0.65, "relevance_note": "Adjacent",
            "adaptation_notes": "Different sector, same ML", "gap_from_base": 1.2,
            "industry_examples": [], "source_citations": [],
        }
        result = _match_vars(match, {})
        assert result["adaptation_notes"] == "Different sector, same ML"
        assert result["gap_from_base"] == 1.2

    def test_match_vars_ambitious_fields(self) -> None:
        from evals.ci_eval import _match_vars
        match = {
            "match_tier": "AMBITIOUS", "source_id": "ind-001",
            "source_title": "Amazon Go", "source_industry": "retail",
            "confidence": 0.50, "relevance_note": "Industry trend",
            "adaptation_notes": "", "gap_from_base": 0.0,
            "industry_examples": ["Amazon", "Walmart"],
            "source_citations": ["McKinsey 2023"],
        }
        result = _match_vars(match, {})
        assert result["industry_examples"] == "Amazon, Walmart"
        assert result["source_citations"] == "McKinsey 2023"

    def test_match_vars_missing_fields_default_safely(self) -> None:
        from evals.ci_eval import _match_vars
        result = _match_vars({}, {})
        assert result["match_tier"] == ""
        assert result["company_industry"] == "unknown"
        assert result["composite_score"] == 0.0


# ── ci_eval _report_vars extracts correct fields ─────────────────────────────

class TestReportVars:
    def _make_state(self, **overrides):
        """Return a minimal mock state object."""
        class _State:
            report = {
                "exec_summary": "Maturity score 2.3.",
                "current_state": "Uses BigQuery.",
                "use_cases": "1. Route Optimization",
                "roadmap": "Phase 1: deploy model.",
                "roi_analysis": "Saves $400K-600K annually.",
            }
            maturity = {"composite_score": 2.3, "composite_label": "Developing"}
            signals = {"industry": "logistics", "scale": "mid-market"}
            use_cases = [{"title": "Route Opt", "tier": "LOW_HANGING_FRUIT"}]
            victory_matches = [{"source_title": "Fleet Routing Win"}]

        state = _State()
        for k, v in overrides.items():
            setattr(state, k, v)
        return state

    def test_report_vars_extracts_report_sections(self) -> None:
        from evals.ci_eval import _report_vars
        state = self._make_state()
        result = _report_vars(state)
        assert result["exec_summary"] == "Maturity score 2.3."
        assert result["current_state"] == "Uses BigQuery."
        assert result["use_cases_section"] == "1. Route Optimization"
        assert result["roadmap"] == "Phase 1: deploy model."
        assert result["roi_analysis"] == "Saves $400K-600K annually."

    def test_report_vars_extracts_maturity_fields(self) -> None:
        from evals.ci_eval import _report_vars
        state = self._make_state()
        result = _report_vars(state)
        assert result["maturity_score"] == 2.3
        assert result["maturity_label"] == "Developing"
        assert result["composite_score"] == 2.3

    def test_report_vars_extracts_signals_fields(self) -> None:
        from evals.ci_eval import _report_vars
        state = self._make_state()
        result = _report_vars(state)
        assert result["company_industry"] == "logistics"

    def test_report_vars_builds_use_cases_summary(self) -> None:
        from evals.ci_eval import _report_vars
        state = self._make_state()
        result = _report_vars(state)
        assert "Route Opt" in result["use_cases_summary"]
        assert "LOW_HANGING_FRUIT" in result["use_cases_summary"]

    def test_report_vars_defaults_on_none_state(self) -> None:
        from evals.ci_eval import _report_vars

        class _Empty:
            report = None
            maturity = None
            signals = None
            use_cases = None
            victory_matches = None

        result = _report_vars(_Empty())
        assert result["exec_summary"] == ""
        assert result["maturity_score"] == 0.0
        assert result["company_industry"] == "unknown"
        assert result["use_cases_summary"] == ""
