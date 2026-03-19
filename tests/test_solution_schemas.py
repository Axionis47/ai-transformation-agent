"""Tests for rag/schemas.py and MatchResult in orchestrator/schemas.py."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from rag.schemas import IndustryCaseStudySchema, SolutionSchema
from orchestrator.schemas import MatchResult, VictoryMatch


def _valid_solution() -> dict:
    return {
        "id": "win-test-001",
        "engagement_title": "Route Optimization for Test Carrier",
        "industry": "logistics",
        "sector_tags": ["ltl_freight"],
        "company_profile": {
            "size_employees": 300,
            "size_label": "mid-market",
            "annual_revenue_usd": "$50M",
            "geography": "US",
            "business_model": "Regional LTL carrier",
        },
        "embed_text": "Test embed text for logistics carrier.",
        "status": "active",
        "ingestion_date": "2026-03-19",
        "solution_category": "predictive_model",
        "applicable_signals": ["ops_signal", "data_signal"],
    }


def _valid_industry_case() -> dict:
    return {
        "id": "ind-test-001",
        "case_title": "Amazon Go Cashierless Checkout",
        "industry": "retail",
        "sector_tags": ["grocery", "checkout"],
        "company_profile": {
            "company_name": "Amazon",
            "company_type": "enterprise",
            "geography": "Global",
            "size_hint": "large enterprise",
        },
        "ai_application": {
            "problem_addressed": "Eliminate checkout wait times",
            "solution_description": "Computer vision cashierless store",
            "technology_used": ["computer_vision", "edge_computing"],
            "deployment_scale": "2,000+ stores",
            "implementation_year": 2018,
        },
        "reported_outcomes": {
            "headline_metric": "Eliminated checkout wait times",
            "supporting_metrics": ["Reduced staff by 30%"],
            "source": "Amazon press release 2021",
            "confidence_in_data": "high",
        },
        "maturity_signal": "Advanced",
        "use_case_category": "computer_vision",
        "embed_text": "Amazon Go cashierless checkout using computer vision.",
        "status": "active",
        "ingestion_date": "2026-03-19",
    }


class TestSolutionSchema:
    def test_validates_valid_record(self):
        record = SolutionSchema(**_valid_solution())
        assert record.id == "win-test-001"
        assert record.status == "active"
        assert record.solution_category == "predictive_model"

    def test_rejects_invalid_status(self):
        data = _valid_solution()
        data["status"] = "unknown_status"
        with pytest.raises(ValidationError):
            SolutionSchema(**data)

    def test_rejects_invalid_solution_category(self):
        data = _valid_solution()
        data["solution_category"] = "magic_model"
        with pytest.raises(ValidationError):
            SolutionSchema(**data)

    def test_defaults_for_new_fields(self):
        """Existing records without new fields should pass with defaults."""
        data = _valid_solution()
        del data["status"]
        del data["ingestion_date"]
        del data["solution_category"]
        del data["applicable_signals"]
        record = SolutionSchema(**data)
        assert record.status == "active"
        assert record.ingestion_date == ""
        assert record.solution_category == "predictive_model"
        assert record.applicable_signals == []

    def test_all_solution_categories_valid(self):
        categories = [
            "predictive_model", "classification", "nlp",
            "computer_vision", "optimization", "scoring_model",
        ]
        for cat in categories:
            data = _valid_solution()
            data["solution_category"] = cat
            record = SolutionSchema(**data)
            assert record.solution_category == cat


class TestIndustryCaseStudySchema:
    def test_validates_valid_record(self):
        record = IndustryCaseStudySchema(**_valid_industry_case())
        assert record.id == "ind-test-001"
        assert record.industry == "retail"
        assert record.use_case_category == "computer_vision"

    def test_rejects_invalid_confidence(self):
        data = _valid_industry_case()
        data["reported_outcomes"]["confidence_in_data"] = "very_high"
        with pytest.raises(ValidationError):
            IndustryCaseStudySchema(**data)

    def test_rejects_invalid_status(self):
        data = _valid_industry_case()
        data["status"] = "retired"
        with pytest.raises(ValidationError):
            IndustryCaseStudySchema(**data)

    def test_defaults_fill_in_missing_fields(self):
        record = IndustryCaseStudySchema(
            id="ind-002", case_title="Test Case", industry="healthcare"
        )
        assert record.status == "active"
        assert record.applicable_signals == []
        assert record.embed_text == ""


class TestMatchResult:
    def test_delivered_tier(self):
        result = MatchResult(
            match_tier="DELIVERED",
            source_id="win-001",
            source_title="Route Optimization",
            confidence=0.90,
        )
        assert result.match_tier == "DELIVERED"
        assert result.confidence == 0.90

    def test_adaptation_tier(self):
        result = MatchResult(
            match_tier="ADAPTATION",
            base_solution_id="win-003",
            adaptation_notes="Different industry domain",
            confidence=0.65,
        )
        assert result.match_tier == "ADAPTATION"
        assert result.base_solution_id == "win-003"

    def test_ambitious_tier(self):
        result = MatchResult(
            match_tier="AMBITIOUS",
            source_library="industry_cases",
            industry_examples=["Amazon", "Walmart"],
            confidence=0.50,
        )
        assert result.match_tier == "AMBITIOUS"
        assert result.source_library == "industry_cases"

    def test_rejects_invalid_tier(self):
        with pytest.raises(ValidationError):
            MatchResult(match_tier="DIRECT_MATCH")

    def test_all_three_tiers_accepted(self):
        for tier in ("DELIVERED", "ADAPTATION", "AMBITIOUS"):
            r = MatchResult(match_tier=tier)
            assert r.match_tier == tier

    def test_victory_match_alias_still_works(self):
        """VictoryMatch must still function as it did before Sprint 8."""
        vm = VictoryMatch(
            win_id="win-001",
            engagement_title="Test",
            match_tier="DIRECT_MATCH",
        )
        assert vm.win_id == "win-001"
        assert vm.match_tier == "DIRECT_MATCH"
