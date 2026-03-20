"""API endpoint tests for user_hints integration."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app import app

_HINTS = {
    "pain_points": ["manual route planning is slow and expensive"],
    "known_tech": ["BigQuery"],
    "industry": "logistics",
}


@pytest.mark.asyncio
async def test_api_accepts_user_hints(monkeypatch):
    """POST /v1/analyze with user_hints returns 200 and complete status."""
    monkeypatch.setenv("DRY_RUN", "true")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/analyze",
            json={"url": "https://example.com", "dry_run": True, "user_hints": _HINTS},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "complete"


@pytest.mark.asyncio
async def test_api_hints_appear_in_signals(monkeypatch):
    """user_hint signals are present in signals.signals when hints are passed."""
    monkeypatch.setenv("DRY_RUN", "true")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/analyze",
            json={"url": "https://example.com", "dry_run": True, "user_hints": _HINTS},
        )

    data = resp.json()
    signals = data.get("signals", {}).get("signals", [])
    sources = {s.get("source") for s in signals}
    assert "user_hint" in sources


@pytest.mark.asyncio
async def test_api_without_hints_no_user_hint_source(monkeypatch):
    """Without hints, no signal carries source=user_hint."""
    monkeypatch.setenv("DRY_RUN", "true")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/analyze",
            json={"url": "https://example.com", "dry_run": True},
        )

    data = resp.json()
    signals = data.get("signals", {}).get("signals", [])
    sources = {s.get("source") for s in signals}
    assert "user_hint" not in sources


@pytest.mark.asyncio
async def test_api_invalid_hints_still_returns_200(monkeypatch):
    """Invalid hints are silently dropped; pipeline still completes."""
    monkeypatch.setenv("DRY_RUN", "true")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/analyze",
            json={
                "url": "https://example.com",
                "dry_run": True,
                "user_hints": {"industry": "martian_mining"},
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "complete"
