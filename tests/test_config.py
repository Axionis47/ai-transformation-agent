"""Tests for core/config.py — config loading, freeze, and env var overrides."""
import os

import pytest

from core.config import freeze_config, load_config


def test_load_config_returns_dict():
    config = load_config()
    assert isinstance(config, dict)


def test_load_config_top_level_keys():
    config = load_config()
    for key in ("budgets", "reasoning", "scoring", "confidence", "models", "gcp"):
        assert key in config, f"Missing top-level key: {key}"


def test_load_config_budget_values():
    config = load_config()
    budgets = config["budgets"]
    assert budgets["external_search_query_budget"] == 10
    assert budgets["external_search_max_calls"] == 8
    assert budgets["rag_query_budget"] == 15
    assert budgets["rag_top_k"] == 5
    assert budgets["rag_min_score"] == pytest.approx(0.3)


def test_load_config_model_values():
    config = load_config()
    models = config["models"]
    assert models["reasoning_model"] == "gemini-2.5-flash"
    assert models["synthesis_model"] == "gemini-2.5-pro"
    assert models["grounding_model"] == "gemini-2.5-flash"


def test_load_config_gcp_values():
    config = load_config()
    gcp = config["gcp"]
    assert gcp["project_id"] == "plotpointe"
    assert gcp["location"] == "us-central1"


def test_freeze_config_returns_dict():
    result = freeze_config()
    assert isinstance(result, dict)


def test_freeze_config_has_all_keys():
    result = freeze_config()
    for key in ("budgets", "reasoning", "scoring", "confidence", "models", "gcp"):
        assert key in result


def test_freeze_config_applies_overrides():
    result = freeze_config(overrides={"models.reasoning_model": "gemini-2.5-pro"})
    assert result["models"]["reasoning_model"] == "gemini-2.5-pro"


def test_freeze_config_nested_budget_override():
    result = freeze_config(overrides={"budgets.rag_query_budget": 20})
    assert result["budgets"]["rag_query_budget"] == 20


def test_freeze_config_no_overrides_unchanged():
    result = freeze_config(overrides=None)
    assert result["budgets"]["rag_query_budget"] == 15


def test_env_var_override_reasoning_model(monkeypatch):
    monkeypatch.setenv("REASONING_MODEL", "gemini-custom-model")
    config = load_config()
    assert config["models"]["reasoning_model"] == "gemini-custom-model"


def test_env_var_override_gcp_project(monkeypatch):
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project-123")
    config = load_config()
    assert config["gcp"]["project_id"] == "test-project-123"
