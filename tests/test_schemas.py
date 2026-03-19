"""Tests for orchestrator/schemas.py and orchestrator/validators.py."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from agents.base import AgentError
from orchestrator.schemas import (
    MaturityResult,
    Signal,
    SignalSet,
    UseCase,
)
from orchestrator.validators import (
    _normalize_signal_sources,
    validate_maturity,
    validate_signals,
    validate_use_cases,
)


# --- Schema round-trip ---

def test_signal_round_trip():
    sig = Signal(type="tech_stack", value="Python", source="job_posting")
    data = sig.model_dump()
    restored = Signal(**data)
    assert restored.type == "tech_stack"
    assert restored.value == "Python"


def test_signal_set_validation():
    signals = [
        Signal(type="tech_stack", value=f"tool-{i}", source="about_text")
        for i in range(5)
    ]
    ss = SignalSet(signals=signals, industry="fintech")
    assert len(ss.signals) == 5
    assert ss.industry == "fintech"


def test_signal_invalid_type():
    with pytest.raises(ValidationError):
        Signal(type="INVALID_TYPE", value="x", source="about_text")


# --- Maturity ---

def _make_maturity_dict() -> dict:
    dim = {"score": 3.0, "signals_used": [], "rationale": "ok"}
    return {
        "dimensions": {
            "data_infrastructure": dim,
            "ml_ai_capability": dim,
            "strategy_intent": dim,
            "operational_readiness": dim,
        },
        "composite_score": 3.0,
        "composite_label": "Developing",
    }


def test_maturity_result_validation():
    result = validate_maturity(_make_maturity_dict())
    assert isinstance(result, MaturityResult)
    assert result.composite_score == 3.0


def test_maturity_missing_dimension():
    data = _make_maturity_dict()
    del data["dimensions"]["ml_ai_capability"]
    result = validate_maturity(data)
    assert isinstance(result, AgentError)
    assert result.code == "VALIDATION_FAIL"
    assert "ml_ai_capability" in result.message


# --- UseCase tiers ---

def test_use_case_tiers():
    for tier in ("LOW_HANGING_FRUIT", "MEDIUM_SOLUTION", "HARD_EXPERIMENT"):
        uc = UseCase(tier=tier, title=f"Test {tier}")
        assert uc.tier == tier


def test_hard_experiment_confidence_cap():
    use_cases = validate_use_cases([
        {"tier": "HARD_EXPERIMENT", "title": "Big bet", "confidence": 0.9},
        {"tier": "LOW_HANGING_FRUIT", "title": "Quick win", "confidence": 0.8},
    ])
    assert not isinstance(use_cases, AgentError)
    hard = next(uc for uc in use_cases if uc.tier == "HARD_EXPERIMENT")
    assert hard.confidence == 0.65


# --- Source normalization ---

def test_source_normalization_known_variants():
    raw = {
        "signals": [
            {"type": "tech_stack", "value": "AWS", "source": "about"},
            {"type": "ml_signal", "value": "PyTorch", "source": "job_postings"},
            {"type": "tech_stack", "value": "API", "source": "product/solutions"},
            {"type": "data_signal", "value": "Kafka", "source": "careers"},
        ],
        "industry": "logistics",
    }
    result = validate_signals(raw)
    assert not isinstance(result, AgentError)
    sources = [s.source for s in result.signals]
    assert sources == ["about_text", "job_posting", "product_page", "careers_page"]


def test_source_normalization_unknown_falls_back_to_about_text():
    raw = {
        "signals": [
            {"type": "tech_stack", "value": "something", "source": "totally_unknown"},
        ],
        "industry": "retail",
    }
    result = validate_signals(raw)
    assert not isinstance(result, AgentError)
    assert result.signals[0].source == "about_text"


def test_normalize_signal_sources_direct():
    data = {"signals": [{"source": "job_postings"}, {"source": "homepage"}]}
    out = _normalize_signal_sources(data)
    assert out["signals"][0]["source"] == "job_posting"
    assert out["signals"][1]["source"] == "about_text"


# --- Signal ID assignment ---

def test_signal_id_assignment():
    data = {
        "signals": [
            {"type": "tech_stack", "value": "AWS", "source": "about_text"},
            {"type": "ml_signal", "value": "TensorFlow", "source": "job_posting"},
            {"type": "data_signal", "value": "Kafka", "source": "product_page"},
        ],
        "industry": "saas",
    }
    result = validate_signals(data)
    assert not isinstance(result, AgentError)
    ids = [s.signal_id for s in result.signals]
    assert ids == ["sig-001", "sig-002", "sig-003"]
    assert result.signal_count == 3
    assert result.confidence_level == "MEDIUM"
