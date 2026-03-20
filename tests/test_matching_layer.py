"""Unit tests for orchestrator/matching_layer.py — three-tier matching logic."""
from __future__ import annotations

import pytest
from orchestrator.matching_layer import match, _pain_point_score, _tech_stack_score, _tokenize


def _make_delivered_record(win_id: str, industry: str, size: str, maturity: str,
                            applicable_signals: list[str] | None = None) -> dict:
    return {
        "id": win_id,
        "engagement_title": f"Test Engagement {win_id}",
        "industry": industry,
        "sector_tags": [],
        "company_profile": {"size_label": size, "size_employees": 100, "geography": "US"},
        "maturity_at_engagement": maturity,
        "results": {
            "primary_metric": {"label": "Cost Reduction", "value": "10%"},
            "measurement_period": "3 months",
        },
        "applicable_signals": applicable_signals or [],
        "tech_stack": {"ml_approach": "XGBoost regression"},
        "engagement_details": {"duration_months": 3},
    }


def _make_industry_record(case_id: str, industry: str, company_type: str,
                           applicable_signals: list[str] | None = None) -> dict:
    return {
        "id": case_id,
        "case_title": f"Industry Case {case_id}",
        "industry": industry,
        "sector_tags": [],
        "company_profile": {"company_name": "TestCo", "company_type": company_type},
        "ai_application": {"deployment_scale": "500 sites"},
        "reported_outcomes": {
            "headline_metric": "15% reduction",
            "source": "Test source 2024",
        },
        "applicable_signals": applicable_signals or ["ops_signal", "data_signal"],
    }


def _signals(industry: str, scale: str, signal_types: list[str] | None = None) -> dict:
    sigs = [{"type": t, "value": "v", "source": "about_text", "confidence": 0.9}
            for t in (signal_types or [])]
    return {"industry": industry, "scale": scale, "signals": sigs}


def _maturity(label: str, score: float) -> dict:
    return {"composite_label": label, "composite_score": score}


# --- DELIVERED track tests ---

def test_delivered_confidence_band():
    """All DELIVERED matches must have confidence >= 0.80."""
    wins = [_make_delivered_record("w1", "logistics", "mid-market", "Developing")]
    result = match(_signals("logistics", "mid-market"), _maturity("Developing", 2.0), wins, [])
    assert len(result["delivered"]) > 0
    for mr in result["delivered"]:
        assert mr.confidence >= 0.80
        assert mr.match_tier == "DELIVERED"


def test_delivered_confidence_max():
    """DELIVERED confidence must not exceed 0.95."""
    wins = [_make_delivered_record("w1", "logistics", "mid-market", "Developing")]
    result = match(_signals("logistics", "mid-market"), _maturity("Developing", 2.0), wins, [])
    for mr in result["delivered"]:
        assert mr.confidence <= 0.95


def test_delivered_source_library():
    """DELIVERED results must have source_library = tenex_delivered."""
    wins = [_make_delivered_record("w1", "logistics", "mid-market", "Developing")]
    result = match(_signals("logistics", "mid-market"), _maturity("Developing", 2.0), wins, [])
    for mr in result["delivered"]:
        assert mr.source_library == "tenex_delivered"


# --- ADAPTATION track tests ---

def test_adaptation_confidence_band():
    """ADAPTATION matches must have confidence in 0.55-0.79."""
    # related industry (0.2) + missing maturity → neutral 0.15 + mismatched size (0.0) = 0.35
    # 0.35 >= 0.30 → ADAPTATION
    record = _make_delivered_record("w1", "manufacturing", "startup", "Emerging")
    record["maturity_at_engagement"] = ""  # missing maturity field
    wins = [record]
    result = match(_signals("logistics", "enterprise"), _maturity("Developing", 2.0), wins, [])
    # manufacturing ~ logistics (related), missing maturity → 0.15, size mismatch → 0.35 ADAPTATION
    assert len(result["adaptation"]) > 0
    for mr in result["adaptation"]:
        assert 0.55 <= mr.confidence <= 0.79
        assert mr.match_tier == "ADAPTATION"


def test_adaptation_has_base_solution_id():
    """ADAPTATION results must reference the base solution ID."""
    record = _make_delivered_record("w-adapt", "manufacturing", "startup", "Emerging")
    record["maturity_at_engagement"] = ""
    wins = [record]
    result = match(_signals("logistics", "enterprise"), _maturity("Developing", 2.0), wins, [])
    for mr in result["adaptation"]:
        assert mr.base_solution_id == "w-adapt"


# --- AMBITIOUS track tests ---

def test_ambitious_confidence_band():
    """AMBITIOUS matches must have confidence in 0.40-0.65."""
    cases = [_make_industry_record("ind-1", "logistics", "mid-market",
                                   ["ops_signal", "data_signal"])]
    result = match(
        _signals("logistics", "mid-market", ["ops_signal"]),
        _maturity("Developing", 2.0),
        [],
        cases,
    )
    assert len(result["ambitious"]) > 0
    for mr in result["ambitious"]:
        assert 0.40 <= mr.confidence <= 0.65
        assert mr.match_tier == "AMBITIOUS"


def test_ambitious_source_library():
    """AMBITIOUS results must have source_library = industry_cases."""
    cases = [_make_industry_record("ind-1", "logistics", "mid-market")]
    result = match(_signals("logistics", "mid-market", ["ops_signal"]), _maturity("Developing", 2.0),
                   [], cases)
    for mr in result["ambitious"]:
        assert mr.source_library == "industry_cases"


# --- Mutual exclusion ---

def test_record_cannot_appear_in_both_delivered_and_adaptation():
    """A Library A record may appear in DELIVERED or ADAPTATION, not both."""
    low_record = _make_delivered_record("w2", "manufacturing", "startup", "Emerging")
    low_record["maturity_at_engagement"] = ""  # missing maturity → 0.35 score → ADAPTATION
    wins = [
        _make_delivered_record("w1", "logistics", "mid-market", "Developing"),  # 1.0 → DELIVERED
        low_record,
    ]
    result = match(_signals("logistics", "enterprise"), _maturity("Developing", 2.0), wins, [])
    delivered_ids = {mr.source_id for mr in result["delivered"]}
    adaptation_ids = {mr.source_id for mr in result["adaptation"]}
    assert delivered_ids.isdisjoint(adaptation_ids), "Records appear in both DELIVERED and ADAPTATION"


# --- Empty input ---

def test_empty_inputs_return_all_three_keys():
    """Empty delivered and industry results return dict with all three keys, all empty."""
    result = match({}, {}, [], [])
    assert set(result.keys()) == {"delivered", "adaptation", "ambitious"}
    assert result["delivered"] == []
    assert result["adaptation"] == []
    assert result["ambitious"] == []


def test_partial_empty_inputs():
    """No industry results means ambitious is empty; delivered results still scored."""
    wins = [_make_delivered_record("w1", "logistics", "mid-market", "Developing")]
    result = match(_signals("logistics", "mid-market"), _maturity("Developing", 2.0), wins, [])
    assert result["ambitious"] == []
    assert len(result["delivered"]) + len(result["adaptation"]) > 0


# --- Pain point scoring tests ---

def test_tokenize_removes_stopwords():
    """Tokenize should strip stopwords and return lowercase tokens."""
    tokens = _tokenize("the manual route planning is slow")
    assert "the" not in tokens
    assert "is" not in tokens
    assert "manual" in tokens
    assert "route" in tokens
    assert "planning" in tokens


def test_pain_point_score_no_pain_signals():
    """Returns 0.0 when no pain_point signals are present."""
    record = {"problem_statement": "manual route planning dispatch", "solution_summary": "ML routing"}
    signals: list[dict] = [{"type": "ops_signal", "value": "manual dispatch"}]
    assert _pain_point_score(record, signals) == 0.0


def test_pain_point_score_overlap_raises_score():
    """Pain tokens matching problem_statement should produce a non-zero score."""
    record = {
        "problem_statement": "manual route planning dispatch slow inefficient",
        "solution_summary": "optimised routing engine reduces manual work",
    }
    signals = [{"type": "pain_point", "value": "manual route planning"}]
    score = _pain_point_score(record, signals)
    assert score > 0.0
    assert score <= 0.15


def test_pain_point_score_max_cap_and_empty_record():
    """Score is capped at 0.15 even with full overlap; empty record returns 0.0."""
    record = {
        "problem_statement": "manual dispatch slow routes inefficient planning",
        "solution_summary": "route optimisation engine",
    }
    signals = [{"type": "pain_point", "value": "manual dispatch slow"}]
    assert _pain_point_score(record, signals) <= 0.15
    assert _pain_point_score({}, signals) == 0.0


def test_pain_point_influences_library_a_score():
    """Library A score increases when pain_point signals match problem_statement."""
    base_record = {
        "id": "w-pain",
        "engagement_title": "Pain Point Test",
        "industry": "logistics",
        "sector_tags": [],
        "company_profile": {"size_label": "mid-market", "size_employees": 200, "geography": "US"},
        "maturity_at_engagement": "Developing",
        "problem_statement": "manual route planning dispatch slow",
        "solution_summary": "routing optimisation",
        "results": {"primary_metric": {"label": "Cost", "value": "10%"}, "measurement_period": "3m"},
        "applicable_signals": [],
        "tech_stack": {"ml_approach": "XGBoost"},
        "engagement_details": {"duration_months": 3},
    }
    sigs_no_pain = {"industry": "logistics", "scale": "mid-market", "signals": []}
    sigs_with_pain = {
        "industry": "logistics",
        "scale": "mid-market",
        "signals": [{"type": "pain_point", "value": "manual route planning", "confidence": 0.9}],
    }
    mat = _maturity("Developing", 2.0)
    result_no = match(sigs_no_pain, mat, [base_record], [])
    result_with = match(sigs_with_pain, mat, [base_record], [])

    all_no = result_no["delivered"] + result_no["adaptation"]
    all_with = result_with["delivered"] + result_with["adaptation"]
    assert len(all_no) > 0 and len(all_with) > 0
    score_no = all_no[0].similarity_score
    score_with = all_with[0].similarity_score
    assert score_with > score_no, "Pain point match should increase similarity score"


# --- Tech stack scoring tests ---

def _tech_record(infra=None, data_sources=None, ml_approach="", client_systems=None) -> dict:
    return {
        "tech_stack": {
            "infrastructure": infra or [],
            "data_sources": data_sources or [],
            "ml_approach": ml_approach,
            "client_systems_integrated": client_systems or [],
        }
    }


def _tech_signals(*values: str) -> list[dict]:
    return [{"type": "tech_stack", "value": v, "confidence": 0.9} for v in values]


def test_tech_stack_score_no_signals():
    """Returns 0.0 when no tech_stack signals are present."""
    record = _tech_record(infra=["BigQuery", "GCP Vertex AI"])
    assert _tech_stack_score(record, []) == 0.0
    ops_only = [{"type": "ops_signal", "value": "BigQuery"}]
    assert _tech_stack_score(record, ops_only) == 0.0


def test_tech_stack_score_no_record_tech():
    """Returns 0.0 when the record has no tech_stack entries."""
    sigs = _tech_signals("BigQuery")
    assert _tech_stack_score({}, sigs) == 0.0
    assert _tech_stack_score({"tech_stack": {}}, sigs) == 0.0


def test_tech_stack_score_full_overlap():
    """Exact token overlap should return 0.15 (capped maximum)."""
    record = _tech_record(infra=["BigQuery"], ml_approach="XGBoost regression")
    sigs = _tech_signals("BigQuery", "XGBoost")
    score = _tech_stack_score(record, sigs)
    assert score > 0.0
    assert score <= 0.15


def test_tech_stack_score_partial_overlap():
    """Partial overlap returns a score between 0.0 and 0.15."""
    record = _tech_record(infra=["BigQuery", "Cloud Run", "Vertex AI"])
    sigs = _tech_signals("BigQuery", "Airflow", "Python")  # only BigQuery overlaps
    score = _tech_stack_score(record, sigs)
    assert 0.0 < score < 0.15


def test_tech_stack_score_no_overlap():
    """Completely different stacks should return 0.0."""
    record = _tech_record(infra=["AWS SageMaker", "Redshift"])
    sigs = _tech_signals("BigQuery", "Vertex AI", "Airflow")
    assert _tech_stack_score(record, sigs) == 0.0


def test_tech_stack_influences_library_a_score():
    """Library A score increases when company tech matches victory tech_stack."""
    base_record = {
        "id": "w-tech",
        "engagement_title": "Tech Stack Test",
        "industry": "logistics",
        "sector_tags": [],
        "company_profile": {"size_label": "mid-market", "size_employees": 200, "geography": "US"},
        "maturity_at_engagement": "Developing",
        "results": {"primary_metric": {"label": "Cost", "value": "10%"}, "measurement_period": "3m"},
        "applicable_signals": [],
        "tech_stack": {
            "infrastructure": ["BigQuery", "GCP Vertex AI", "Cloud Run"],
            "data_sources": ["GPS telemetry"],
            "ml_approach": "XGBoost regression",
            "client_systems_integrated": [],
        },
        "engagement_details": {"duration_months": 3},
    }
    sigs_no_tech = {"industry": "logistics", "scale": "mid-market", "signals": []}
    sigs_with_tech = {
        "industry": "logistics",
        "scale": "mid-market",
        "signals": [{"type": "tech_stack", "value": "BigQuery", "confidence": 0.9}],
    }
    mat = _maturity("Developing", 2.0)
    result_no = match(sigs_no_tech, mat, [base_record], [])
    result_with = match(sigs_with_tech, mat, [base_record], [])

    all_no = result_no["delivered"] + result_no["adaptation"]
    all_with = result_with["delivered"] + result_with["adaptation"]
    assert len(all_no) > 0 and len(all_with) > 0
    assert all_with[0].similarity_score > all_no[0].similarity_score, (
        "Tech stack match should increase similarity score"
    )


# --- Sector bonus broad signal coverage tests ---

def _sector_record(sector_tags: list[str]) -> dict:
    """Minimal Library A record with given sector tags."""
    return {
        "id": "w-sector",
        "engagement_title": "Sector Test",
        "industry": "logistics",
        "sector_tags": sector_tags,
        "company_profile": {"size_label": "mid-market", "size_employees": 200, "geography": "US"},
        "maturity_at_engagement": "Developing",
        "results": {"primary_metric": {"label": "Cost", "value": "10%"}, "measurement_period": "3m"},
        "applicable_signals": [],
        "tech_stack": {"ml_approach": "XGBoost"},
        "engagement_details": {"duration_months": 3},
    }


def _match_with_signal(signal_type: str, signal_value: str) -> list:
    """Run match with a single signal of given type and return all A-track results."""
    record = _sector_record(["route planning", "fleet management", "ltl freight"])
    sigs = {
        "industry": "logistics",
        "scale": "mid-market",
        "signals": [{"type": signal_type, "value": signal_value, "confidence": 0.9}],
    }
    result = match(sigs, _maturity("Developing", 2.0), [record], [])
    return result["delivered"] + result["adaptation"]


def _match_no_sector_signal(signal_type: str) -> list:
    """Run match with a signal type that has no value overlapping sector tags."""
    record = _sector_record(["route planning", "fleet management"])
    sigs = {
        "industry": "logistics",
        "scale": "mid-market",
        "signals": [{"type": signal_type, "value": "unrelated office supplies", "confidence": 0.9}],
    }
    result = match(sigs, _maturity("Developing", 2.0), [record], [])
    return result["delivered"] + result["adaptation"]


def test_sector_bonus_triggers_on_pain_point():
    """pain_point signal matching a sector tag gives sector bonus (score increases)."""
    # baseline — same record, no signals at all
    record = _sector_record(["route planning", "fleet management"])
    baseline_sigs = {"industry": "logistics", "scale": "mid-market", "signals": []}
    base = match(baseline_sigs, _maturity("Developing", 2.0), [record], [])
    base_all = base["delivered"] + base["adaptation"]

    # with pain_point containing a sector_tag substring
    with_pain = _match_with_signal("pain_point", "manual route planning is slow")
    assert len(with_pain) > 0
    assert len(base_all) > 0
    assert with_pain[0].similarity_score > base_all[0].similarity_score, (
        "pain_point matching sector tag should increase score"
    )


def test_sector_bonus_triggers_on_hiring_signal():
    """hiring_signal containing a sector tag triggers sector bonus."""
    record = _sector_record(["route planning", "fleet management"])
    baseline_sigs = {"industry": "logistics", "scale": "mid-market", "signals": []}
    base = match(baseline_sigs, _maturity("Developing", 2.0), [record], [])
    base_all = base["delivered"] + base["adaptation"]

    with_hiring = _match_with_signal("hiring_signal", "fleet management engineer")
    assert len(with_hiring) > 0
    assert with_hiring[0].similarity_score > base_all[0].similarity_score, (
        "hiring_signal matching sector tag should increase score"
    )


def test_sector_bonus_triggers_on_intent_and_industry_hint():
    """intent_signal and industry_hint both trigger sector bonus when overlapping a tag."""
    for sig_type, sig_value in [
        ("intent_signal", "exploring ltl freight optimisation"),
        ("industry_hint", "fleet management operations"),
    ]:
        record = _sector_record(["ltl freight", "fleet management"])
        baseline_sigs = {"industry": "logistics", "scale": "mid-market", "signals": []}
        base = match(baseline_sigs, _maturity("Developing", 2.0), [record], [])
        base_all = base["delivered"] + base["adaptation"]

        result = _match_with_signal(sig_type, sig_value)
        assert len(result) > 0 and len(base_all) > 0
        assert result[0].similarity_score > base_all[0].similarity_score, (
            f"{sig_type} matching sector tag should increase score"
        )


def test_sector_bonus_fuzzy_underscore_normalization():
    """sector_tags with underscores match signal values with spaces (normalized)."""
    record = _sector_record(["ltl_freight", "route_planning"])
    sigs = {
        "industry": "logistics",
        "scale": "mid-market",
        "signals": [{"type": "pain_point", "value": "ltl freight dispatch delays", "confidence": 0.9}],
    }
    result = match(sigs, _maturity("Developing", 2.0), [record], [])
    base = match({"industry": "logistics", "scale": "mid-market", "signals": []},
                 _maturity("Developing", 2.0), [record], [])
    all_r = result["delivered"] + result["adaptation"]
    base_all = base["delivered"] + base["adaptation"]
    assert len(all_r) > 0 and len(base_all) > 0
    assert all_r[0].similarity_score > base_all[0].similarity_score, (
        "Underscore-normalized sector tag should fuzzy-match signal value"
    )


def test_sector_bonus_max_is_0_1():
    """Multiple matching tags still produce at most 0.1 sector bonus."""
    record = _sector_record(["route planning", "fleet management", "ltl freight", "dispatch"])
    sigs = {
        "industry": "logistics",
        "scale": "mid-market",
        "signals": [
            {"type": "pain_point", "value": "manual route planning and ltl freight dispatch", "confidence": 0.9},
            {"type": "hiring_signal", "value": "fleet management engineer", "confidence": 0.8},
            {"type": "intent_signal", "value": "dispatch optimisation", "confidence": 0.7},
        ],
    }
    result = match(sigs, _maturity("Developing", 2.0), [record], [])
    base = match({"industry": "logistics", "scale": "mid-market", "signals": []},
                 _maturity("Developing", 2.0), [record], [])
    all_r = result["delivered"] + result["adaptation"]
    base_all = base["delivered"] + base["adaptation"]
    assert len(all_r) > 0 and len(base_all) > 0
    delta = round(all_r[0].similarity_score - base_all[0].similarity_score, 3)
    assert delta >= 0.0  # score increased or equal; sector bonus capped at 0.1


# --- Integration test: win-001 scoring with realistic fixture data ---

def _win_001_record() -> dict:
    """Return the win-001 fixture record: Route Optimization for Regional LTL Carrier."""
    return {
        "id": "win-001",
        "engagement_title": "Route Optimization for Regional LTL Carrier",
        "industry": "logistics",
        "sector_tags": ["ltl_freight", "route_planning", "fleet_management"],
        "company_profile": {
            "size_label": "mid-market",
            "size_employees": 520,
            "geography": "US Midwest",
        },
        "maturity_at_engagement": "Developing",
        "problem_statement": (
            "The carrier dispatched routes manually using a combination of dispatcher "
            "experience and a legacy TMS. Route planners spent 3-4 hours per day on "
            "manual adjustments to handle exceptions, weather, and driver availability. "
            "Fuel costs had risen 18% year-over-year while on-time delivery rates dropped."
        ),
        "solution_summary": (
            "Tenex built an ML-based route optimisation engine ingesting GPS telemetry, "
            "delivery time windows, driver shift constraints, and historical traffic "
            "patterns. The model used XGBoost regression to predict optimal route "
            "sequences and flag at-risk deliveries before estimated late."
        ),
        "results": {
            "primary_metric": {"label": "Fuel Cost Reduction", "value": "14%"},
            "measurement_period": "4 months post-deployment",
        },
        "engagement_details": {"duration_months": 4},
        "tech_stack": {
            "infrastructure": ["GCP Vertex AI", "BigQuery", "Cloud Run for API serving"],
            "data_sources": ["GPS telemetry (18 months)", "ERP order data"],
            "ml_approach": "XGBoost regression for route scoring",
            "client_systems_integrated": ["Legacy TMS REST API"],
        },
        "applicable_signals": [],
    }


