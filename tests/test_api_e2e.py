"""API response shape test for Sprint 4 pipeline."""
import pytest
from httpx import AsyncClient, ASGITransport

from app import app


@pytest.mark.asyncio
async def test_api_returns_sprint4_fields(monkeypatch):
    """POST /v1/analyze dry-run returns all Sprint 4 fields."""
    monkeypatch.setenv("DRY_RUN", "true")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/analyze", json={"url": "https://example.com", "dry_run": True}
        )

    assert resp.status_code == 200
    data = resp.json()

    # Core fields
    assert data["status"] == "complete"
    assert "report" in data

    # Sprint 4 fields present
    assert "signals" in data
    assert "maturity" in data
    assert "victory_matches" in data
    assert "use_cases" in data

    # Signals shape
    sigs = data["signals"].get("signals", [])
    assert len(sigs) > 0 or data["signals"].get("signal_count", 0) > 0

    # Maturity shape
    assert "composite_score" in data["maturity"]
    assert "dimensions" in data["maturity"]

    # Use cases shape
    assert len(data["use_cases"]) >= 2
    tiers = {uc["tier"] for uc in data["use_cases"]}
    assert "LOW_HANGING_FRUIT" in tiers

    # Victory matches shape — now MatchResult (Sprint 8 schema)
    for vm in data["victory_matches"]:
        assert "match_tier" in vm
        # MatchResult uses source_id; VictoryMatch (legacy) used win_id
        assert "source_id" in vm or "win_id" in vm


@pytest.mark.asyncio
async def test_api_report_sections_present(monkeypatch):
    """Report contains all 5 required sections with content."""
    monkeypatch.setenv("DRY_RUN", "true")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/analyze", json={"url": "https://example.com", "dry_run": True}
        )

    data = resp.json()
    for section in ["exec_summary", "current_state", "use_cases", "roadmap", "roi_analysis"]:
        assert section in data["report"], f"Missing report section: {section}"
        assert len(data["report"][section]) > 50, f"Section too short: {section}"


@pytest.mark.asyncio
async def test_api_backward_compat_analysis(monkeypatch):
    """analysis field is still returned for backward compatibility."""
    monkeypatch.setenv("DRY_RUN", "true")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/analyze", json={"url": "https://example.com", "dry_run": True}
        )

    data = resp.json()
    assert "analysis" in data
    assert data["analysis"] is not None
    assert "maturity_score" in data["analysis"]
    assert "maturity_label" in data["analysis"]
