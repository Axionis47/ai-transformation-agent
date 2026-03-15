"""Tests for ops/model_client.py — MockProvider dry-run and factory."""

import os

from ops.model_client import MockProvider, get_model_client


def test_mock_provider_returns_string():
    provider = MockProvider()
    result = provider.complete("test prompt")
    assert isinstance(result, str)
    assert len(result) > 0


def test_dry_run_factory_returns_mock(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    client = get_model_client()
    assert isinstance(client, MockProvider)


def test_mock_factory_explicit(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "mock")
    monkeypatch.delenv("DRY_RUN", raising=False)
    client = get_model_client()
    assert isinstance(client, MockProvider)
