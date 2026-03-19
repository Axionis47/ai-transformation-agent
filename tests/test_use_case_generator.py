"""Tests for UseCaseGeneratorAgent — per-tier synthesis and fixture coverage."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_use_cases.json"
_TIER_ORDER = ["LOW_HANGING_FRUIT", "MEDIUM_SOLUTION", "HARD_EXPERIMENT"]


def test_fixture_contains_all_three_tiers():
    """Fixture must have exactly one use case per tier."""
    data = json.loads(_FIXTURE.read_text())
    tiers = [uc["tier"] for uc in data]
    for expected in _TIER_ORDER:
        assert expected in tiers, f"Fixture missing tier: {expected}"


def test_fixture_tier_order():
    """Use cases are ordered LOW_HANGING_FRUIT -> MEDIUM_SOLUTION -> HARD_EXPERIMENT."""
    data = json.loads(_FIXTURE.read_text())
    tiers = [uc["tier"] for uc in data]
    assert tiers == _TIER_ORDER, f"Expected ordered tiers {_TIER_ORDER}, got {tiers}"


def test_hard_experiment_has_industry_reference():
    """HARD_EXPERIMENT use case must cite an industry case (ind-NNN) in rag_benchmark."""
    data = json.loads(_FIXTURE.read_text())
    hard = next(uc for uc in data if uc["tier"] == "HARD_EXPERIMENT")
    assert hard.get("rag_benchmark"), "HARD_EXPERIMENT missing rag_benchmark"
    assert "ind-" in hard["rag_benchmark"], (
        f"HARD_EXPERIMENT rag_benchmark should cite ind-NNN, got: {hard['rag_benchmark']}"
    )


def test_dry_run_returns_all_three_tiers(monkeypatch):
    """Dry-run returns fixture with all three tier types."""
    monkeypatch.setenv("DRY_RUN", "true")
    from agents.use_case_generator import UseCaseGeneratorAgent

    agent = UseCaseGeneratorAgent()
    result = agent.run({"signals": [], "maturity": {}, "victory_matches": []})

    assert isinstance(result, list), "Expected list"
    tiers = [uc.get("tier") for uc in result]
    for expected in _TIER_ORDER:
        assert expected in tiers, f"Dry-run missing tier: {expected}"


def test_dry_run_uses_fixture_regardless_of_match_results(monkeypatch):
    """Dry-run ignores match_results and reads from fixture."""
    monkeypatch.setenv("DRY_RUN", "true")
    from agents.use_case_generator import UseCaseGeneratorAgent

    agent = UseCaseGeneratorAgent()
    result = agent.run({
        "signals": [],
        "maturity": {},
        "victory_matches": [],
        "match_results": {"delivered": [], "adaptation": [], "ambitious": []},
    })

    assert isinstance(result, list)
    tiers = [uc.get("tier") for uc in result]
    assert "LOW_HANGING_FRUIT" in tiers


def test_build_tier_prompt_includes_tier_key(monkeypatch):
    """_build_tier_prompt includes the tier key label in the prompt text."""
    monkeypatch.setenv("DRY_RUN", "false")
    from agents.use_case_generator import UseCaseGeneratorAgent

    agent = UseCaseGeneratorAgent()
    prompt = agent._build_tier_prompt(
        signals=[{"signal_id": "sig-001", "type": "tech_stack", "value": "BigQuery"}],
        maturity={"composite_score": 2.0, "composite_label": "Developing"},
        records=[{"source_id": "win-001", "match_tier": "DELIVERED"}],
        tier_key="delivered",
    )

    assert "delivered" in prompt
    assert "sig-001" in prompt
    assert "win-001" in prompt


def test_per_tier_prompt_files_exist():
    """All three tier prompt files must exist on disk."""
    prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
    for fname in ("tier1_delivered.md", "tier2_adaptation.md", "tier3_ambitious.md"):
        assert (prompts_dir / fname).exists(), f"Missing prompt file: {fname}"


def test_load_tier_prompt_returns_string(monkeypatch):
    """_load_tier_prompt returns non-empty string for each tier key."""
    monkeypatch.setenv("DRY_RUN", "false")
    from agents.use_case_generator import UseCaseGeneratorAgent

    agent = UseCaseGeneratorAgent()
    for key in ("delivered", "adaptation", "ambitious"):
        content = agent._load_tier_prompt(key)
        assert isinstance(content, str) and len(content) > 50, (
            f"Tier prompt for '{key}' is empty or missing"
        )
