"""Tests for rate limiter behavior and GCS trace persistence."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from infra.rate_limiter import RateLimiter, reset_limiter


# ---------------------------------------------------------------------------
# RateLimiter unit tests
# ---------------------------------------------------------------------------


def test_rate_limiter_allows_first_request():
    rl = RateLimiter(max_requests=5, window_seconds=60)
    allowed, retry_after = rl.check("user1")
    assert allowed is True
    assert retry_after == 0


def test_rate_limiter_blocks_after_max_requests():
    rl = RateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        allowed, _ = rl.check("user1")
        assert allowed is True
    allowed, retry_after = rl.check("user1")
    assert allowed is False
    assert retry_after > 0


def test_rate_limiter_independent_per_user():
    rl = RateLimiter(max_requests=2, window_seconds=60)
    for _ in range(2):
        rl.check("userA")
    assert rl.check("userA")[0] is False
    assert rl.check("userB")[0] is True


def test_rate_limiter_reset_clears_state():
    rl = RateLimiter(max_requests=1, window_seconds=60)
    rl.check("user1")
    assert rl.check("user1")[0] is False
    rl.reset()
    assert rl.check("user1")[0] is True


def test_rate_limiter_disabled_when_max_zero():
    rl = RateLimiter(max_requests=0, window_seconds=60)
    for _ in range(50):
        allowed, retry_after = rl.check("user1")
        assert allowed is True
        assert retry_after == 0


def test_rate_limiter_window_evicts_old_entries():
    rl = RateLimiter(max_requests=2, window_seconds=1)
    rl.check("user1")
    rl.check("user1")
    assert rl.check("user1")[0] is False
    old_time = time.time() - 2
    with rl._lock:
        rl._requests["user1"] = [old_time, old_time]
    assert rl.check("user1")[0] is True


def test_rate_limiter_singleton_disabled_in_dev():
    """Singleton disables rate limiting when GOOGLE_AUTH_ENABLED is off."""
    reset_limiter()
    from infra.rate_limiter import get_rate_limiter
    rl = get_rate_limiter()
    assert rl._max == 0
    assert rl.check("any-user")[0] is True
    reset_limiter()


# ---------------------------------------------------------------------------
# GCS trace flush tests
# ---------------------------------------------------------------------------


def test_flush_to_gcs_noop_when_no_bucket(tmp_path, monkeypatch):
    monkeypatch.delenv("GCS_TRACE_BUCKET", raising=False)
    from ops.logger import PipelineLogger

    logger = PipelineLogger.__new__(PipelineLogger)
    logger.run_id = "run-abc"
    logger._path = tmp_path / "run-abc.jsonl"
    logger._path.write_text('{"event": "test"}\n')

    with patch("google.cloud.storage.Client") as mock_client:
        logger.flush_to_gcs("run-abc")
        mock_client.assert_not_called()


def test_flush_to_gcs_uploads_when_bucket_set(tmp_path, monkeypatch):
    monkeypatch.setenv("GCS_TRACE_BUCKET", "my-test-bucket")
    from ops.logger import PipelineLogger

    logger = PipelineLogger.__new__(PipelineLogger)
    logger.run_id = "run-xyz"
    logger._path = tmp_path / "run-xyz.jsonl"
    logger._path.write_text('{"event": "agent_complete"}\n')

    mock_blob = MagicMock()
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_client_instance = MagicMock()
    mock_client_instance.bucket.return_value = mock_bucket

    with patch("google.cloud.storage.Client", return_value=mock_client_instance):
        logger.flush_to_gcs("run-xyz")

    mock_client_instance.bucket.assert_called_once_with("my-test-bucket")
    mock_bucket.blob.assert_called_once_with("traces/run-xyz.jsonl")
    mock_blob.upload_from_filename.assert_called_once_with(str(logger._path))


def test_flush_to_gcs_noop_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("GCS_TRACE_BUCKET", "my-bucket")
    from ops.logger import PipelineLogger

    logger = PipelineLogger.__new__(PipelineLogger)
    logger.run_id = "run-missing"
    logger._path = tmp_path / "run-missing.jsonl"

    with patch("google.cloud.storage.Client") as mock_client:
        logger.flush_to_gcs("run-missing")
        mock_client.assert_not_called()


def test_flush_to_gcs_swallows_gcs_errors(tmp_path, monkeypatch):
    monkeypatch.setenv("GCS_TRACE_BUCKET", "broken-bucket")
    from ops.logger import PipelineLogger

    logger = PipelineLogger.__new__(PipelineLogger)
    logger.run_id = "run-err"
    logger._path = tmp_path / "run-err.jsonl"
    logger._path.write_text('{"event": "test"}\n')

    with patch("google.cloud.storage.Client", side_effect=Exception("GCS down")):
        logger.flush_to_gcs("run-err")  # must not raise
