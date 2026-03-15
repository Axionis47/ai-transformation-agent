"""Tests for ops/model_client.py — MockProvider dry-run and factory."""

import os

from ops.model_client import MockProvider, VertexProvider, get_model_client


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


def test_strip_code_fences_json_block():
    provider = VertexProvider()
    fenced = '```json\n{"key": "value"}\n```'
    result = provider._strip_code_fences(fenced)
    assert result == '{"key": "value"}'


def test_strip_code_fences_plain_block():
    provider = VertexProvider()
    fenced = '```\n{"key": "value"}\n```'
    result = provider._strip_code_fences(fenced)
    assert result == '{"key": "value"}'


def test_strip_code_fences_no_fence():
    provider = VertexProvider()
    plain = '{"key": "value"}'
    result = provider._strip_code_fences(plain)
    assert result == '{"key": "value"}'


def test_strip_code_fences_preserves_whitespace_inside():
    provider = VertexProvider()
    fenced = '```json\n{\n  "a": 1\n}\n```'
    result = provider._strip_code_fences(fenced)
    assert result == '{\n  "a": 1\n}'
