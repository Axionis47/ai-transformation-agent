"""Tests for app.py — FastAPI endpoint coverage."""

from __future__ import annotations

from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app import app
from orchestrator.state import PipelineState, PipelineStatus


@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.mark.asyncio
async def test_health_check(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"


@pytest.mark.asyncio
async def test_analyze_dry_run(monkeypatch, transport):
    monkeypatch.setenv("DRY_RUN", "true")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/analyze", json={"url": "https://example.com", "dry_run": True}
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "complete"
    assert "report" in body
    for section in ["exec_summary", "current_state", "use_cases", "roadmap", "roi_analysis"]:
        assert section in body["report"], f"Missing report section: {section}"
    assert "analysis" in body, "Response missing 'analysis' field"
    assert body["analysis"] is not None, "analysis field is null"
    assert "maturity_score" in body["analysis"], "analysis missing maturity_score"


@pytest.mark.asyncio
async def test_analyze_validation(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/v1/analyze", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_analyze_failure(transport):
    failed_state = PipelineState(
        url="https://bad.com",
        status=PipelineStatus.FAILED,
        error={"code": "SCRAPE_ERROR", "message": "Connection refused", "agent": "scraper"},
    )

    with patch("app.run_pipeline", return_value=failed_state):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/v1/analyze", json={"url": "https://bad.com", "dry_run": False}
            )

    assert resp.status_code == 500
    body = resp.json()
    assert "error" in body["detail"]
    assert body["detail"]["error"]["code"] == "SCRAPE_ERROR"
