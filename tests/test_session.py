"""Tests for the Analyst Copilot session system."""
import json
from pathlib import Path

import pytest

from agents.input_parser import InputParserAgent, _dry_run_parse
from agents.victory_assessor import VictoryAssessorAgent
from orchestrator.reasoning_engine import (
    classify_recommendations,
    process_turn,
)
from orchestrator.session_schemas import (
    Recommendations,
    SessionState,
    TargetedQuestion,
    VictoryAssessment,
)
from services.victory_service import VictoryService


# --- Schema tests ---

class TestSessionSchemas:
    def test_session_state_defaults(self):
        state = SessionState()
        assert state.session_id
        assert state.company_name == ""
        assert state.pain_points == []
        assert state.matched_victories == []
        assert state.recommendations is None

    def test_session_state_with_data(self):
        state = SessionState(
            company_name="Acme Corp",
            industry="financial_services",
            size_label="mid-market",
            employee_count=500,
            pain_points=["manual invoicing"],
        )
        assert state.company_name == "Acme Corp"
        assert state.employee_count == 500
        assert len(state.pain_points) == 1

    def test_victory_assessment_model(self):
        va = VictoryAssessment(
            victory_id="win-001",
            victory_title="Test Victory",
            tier="EASY_WIN",
            confidence=0.9,
        )
        assert va.tier == "EASY_WIN"
        assert va.confidence == 0.9

    def test_recommendations_model(self):
        easy = VictoryAssessment(victory_id="w1", tier="EASY_WIN", confidence=0.9)
        mod = VictoryAssessment(victory_id="w2", tier="MODERATE_WIN", confidence=0.6)
        recs = Recommendations(easy_wins=[easy], moderate_wins=[mod])
        assert len(recs.easy_wins) == 1
        assert len(recs.moderate_wins) == 1


# --- Input parser tests ---

class TestInputParser:
    def test_dry_run_parse_tech(self):
        result = _dry_run_parse("They use SAP for ERP and Oracle DB.")
        assert "SAP" in result["known_tech"]
        assert "Oracle" in result["known_tech"]

    def test_dry_run_parse_pitch_command(self):
        result = _dry_run_parse("generate pitch")
        assert result["generate_pitch"] is True

    def test_dry_run_parse_employee_count(self):
        result = _dry_run_parse("About 900 employees in the company.")
        assert result["employee_count"] == 900

    def test_dry_run_parse_context_keywords(self):
        result = _dry_run_parse("They are regulated by OCC and FDIC.")
        assert "OCC" in result["context_notes"]
        assert "FDIC" in result["context_notes"]

    def test_dry_run_parse_explicit_query(self):
        result = _dry_run_parse("What about document processing?")
        assert len(result["explicit_queries"]) == 1

    def test_agent_empty_message(self):
        agent = InputParserAgent()
        result = agent.run({"message": "", "dry_run": True})
        assert result.code == "EMPTY_INPUT"

    def test_agent_first_turn_fixture(self):
        agent = InputParserAgent()
        result = agent.run({
            "message": "Cross River Bank, mid-market bank.",
            "session_summary": "",
            "dry_run": True,
            "is_first_turn": True,
        })
        assert result["company_name"] == "Cross River Bank"
        assert result["industry"] == "financial_services"

    def test_agent_subsequent_turn(self):
        agent = InputParserAgent()
        result = agent.run({
            "message": "They use SAP for ERP.",
            "session_summary": "Company: Cross River Bank",
            "dry_run": True,
            "is_first_turn": False,
        })
        assert "SAP" in result["known_tech"]


# --- Victory assessor tests ---

class TestVictoryAssessor:
    def test_dry_run_assessment(self):
        agent = VictoryAssessorAgent()
        result = agent.run({
            "victory": {"id": "win-001", "engagement_title": "Test"},
            "company": {"company_name": "Acme"},
            "dry_run": True,
        })
        assert result["victory_id"] == "win-001"
        assert result["tier"] in ("EASY_WIN", "MODERATE_WIN", "AMBITIOUS")

    def test_no_victory_error(self):
        agent = VictoryAssessorAgent()
        result = agent.run({"victory": {}, "company": {}, "dry_run": True})
        assert result.code == "NO_VICTORY"


# --- Victory service tests ---

class TestVictoryService:
    def test_query_victories_dry_run(self):
        svc = VictoryService(dry_run=True)
        results = svc.query_victories("financial services invoice", k=3)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_query_industry_cases_dry_run(self):
        svc = VictoryService(dry_run=True)
        results = svc.query_industry_cases("financial services", k=2)
        assert isinstance(results, list)

    def test_get_all_victories_dry_run(self):
        svc = VictoryService(dry_run=True)
        results = svc.get_all_victories()
        assert isinstance(results, list)
        assert len(results) > 0


# --- Classify recommendations tests ---

class TestClassifyRecommendations:
    def test_sorts_into_tiers(self):
        assessments = [
            VictoryAssessment(victory_id="w1", tier="EASY_WIN", confidence=0.9),
            VictoryAssessment(victory_id="w2", tier="MODERATE_WIN", confidence=0.7),
            VictoryAssessment(victory_id="w3", tier="AMBITIOUS", confidence=0.4),
            VictoryAssessment(victory_id="w4", tier="EASY_WIN", confidence=0.85),
        ]
        recs = classify_recommendations(assessments)
        assert len(recs.easy_wins) == 2
        assert len(recs.moderate_wins) == 1
        assert len(recs.ambitious) == 1
        assert recs.easy_wins[0].confidence >= recs.easy_wins[1].confidence

    def test_generates_questions_from_missing(self):
        assessments = [
            VictoryAssessment(
                victory_id="w1", tier="EASY_WIN", confidence=0.9,
                victory_title="Invoice Auto",
                key_question="What ERP?", missing=["ERP unknown"],
            ),
        ]
        recs = classify_recommendations(assessments)
        assert len(recs.top_questions) == 1
        assert recs.top_questions[0].victory_id == "w1"

    def test_empty_assessments(self):
        recs = classify_recommendations([])
        assert len(recs.easy_wins) == 0
        assert len(recs.moderate_wins) == 0
        assert len(recs.ambitious) == 0


# --- Reasoning engine integration tests ---

class TestReasoningEngine:
    def test_full_session_dry_run(self):
        state = SessionState(company_name="Cross River Bank", dry_run=True)
        r1 = process_turn(state, "Mid-market bank, ~900 employees. Manual invoice processing.")
        assert "win-001" in r1 or "Invoice" in r1
        assert len(state.matched_victories) > 0
        assert state.recommendations is not None

    def test_tech_update_turn(self):
        state = SessionState(
            company_name="Cross River Bank",
            industry="financial_services",
            dry_run=True,
        )
        process_turn(state, "Mid-market bank, manual invoice processing.")
        initial_count = len(state.matched_victories)
        r2 = process_turn(state, "They use SAP for ERP.")
        assert "SAP" in state.known_tech
        assert "SAP" in r2 or "confirmed" in r2.lower()

    def test_pitch_generation(self):
        state = SessionState(
            company_name="Cross River Bank",
            industry="financial_services",
            dry_run=True,
        )
        process_turn(state, "Mid-market bank, manual invoice processing.")
        pitch = process_turn(state, "Generate pitch")
        assert "Cross River Bank" in pitch
        assert "Easy Wins" in pitch or "EASY" in pitch

    def test_context_notes_accumulated(self):
        state = SessionState(company_name="Test Corp", dry_run=True)
        process_turn(state, "Test Corp. 500 employees.")
        process_turn(state, "They are a BaaS provider regulated by OCC.")
        assert "OCC" in state.context_notes
        assert "BaaS" in state.context_notes

    def test_session_not_found_404(self):
        from app import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        r = client.post("/v2/session/nonexistent/turn", json={"message": "hi"})
        assert r.status_code == 404


# --- API endpoint tests ---

class TestSessionAPI:
    @pytest.fixture
    def client(self):
        from app import app
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_create_session(self, client):
        r = client.post("/v2/session", json={"company_name": "Acme", "dry_run": True})
        assert r.status_code == 200
        data = r.json()
        assert "session_id" in data
        assert "system_message" in data

    def test_session_turn(self, client):
        r1 = client.post("/v2/session", json={"company_name": "Acme", "dry_run": True})
        sid = r1.json()["session_id"]
        r2 = client.post(f"/v2/session/{sid}/turn", json={"message": "500 employees, manual invoicing."})
        assert r2.status_code == 200
        data = r2.json()
        assert "system_message" in data
        assert "recommendations" in data
        assert data["turn_count"] >= 1

    def test_generate_pitch_endpoint(self, client):
        r1 = client.post("/v2/session", json={"company_name": "Acme", "dry_run": True})
        sid = r1.json()["session_id"]
        client.post(f"/v2/session/{sid}/turn", json={"message": "500 employees, manual invoicing."})
        r3 = client.post(f"/v2/session/{sid}/pitch")
        assert r3.status_code == 200
        data = r3.json()
        assert "pitch" in data
        assert "easy_wins" in data

    def test_multi_turn_session(self, client):
        r1 = client.post("/v2/session", json={"company_name": "Test Bank", "dry_run": True})
        sid = r1.json()["session_id"]

        client.post(f"/v2/session/{sid}/turn", json={"message": "Mid-market bank, ~900 employees."})
        r3 = client.post(f"/v2/session/{sid}/turn", json={"message": "They use SAP and Oracle."})
        data = r3.json()
        assert data["turn_count"] >= 2
