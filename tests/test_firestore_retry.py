"""Tests for Firestore save_run retry logic."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def test_firestore_save_retries_on_transient_error():
    """save_run retries on ServiceUnavailable and eventually succeeds."""
    from google.api_core.exceptions import ServiceUnavailable
    from infra.auth import User
    from infra.firestore_store import FirestoreStore

    store = FirestoreStore()
    mock_db = MagicMock()
    store._db = mock_db

    doc_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = doc_ref
    doc_ref.set.side_effect = [
        ServiceUnavailable("timeout"),
        ServiceUnavailable("timeout"),
        None,
    ]

    user = User(uid="u1", email="u@example.com", name="U")
    with patch("time.sleep"):
        store.save_run("run-001", {"report": {}}, user)

    assert doc_ref.set.call_count == 3


def test_firestore_save_raises_after_all_retries_exhausted():
    """save_run raises if all 3 attempts fail with transient errors."""
    from google.api_core.exceptions import ServiceUnavailable
    from infra.auth import User
    from infra.firestore_store import FirestoreStore

    store = FirestoreStore()
    mock_db = MagicMock()
    store._db = mock_db

    doc_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = doc_ref
    doc_ref.set.side_effect = ServiceUnavailable("always fails")

    user = User(uid="u1", email="u@example.com", name="U")
    with patch("time.sleep"), pytest.raises(ServiceUnavailable):
        store.save_run("run-002", {}, user)

    assert doc_ref.set.call_count == 3


def test_firestore_save_no_retry_on_permission_denied():
    """save_run does NOT retry on PermissionDenied — propagates immediately."""
    from google.api_core.exceptions import PermissionDenied
    from infra.auth import User
    from infra.firestore_store import FirestoreStore

    store = FirestoreStore()
    mock_db = MagicMock()
    store._db = mock_db

    doc_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = doc_ref
    doc_ref.set.side_effect = PermissionDenied("denied")

    user = User(uid="u1", email="u@example.com", name="U")
    with pytest.raises(PermissionDenied):
        store.save_run("run-003", {}, user)

    assert doc_ref.set.call_count == 1


def test_firestore_save_retries_aborted():
    """save_run retries on Aborted (optimistic lock conflict)."""
    from google.api_core.exceptions import Aborted
    from infra.auth import User
    from infra.firestore_store import FirestoreStore

    store = FirestoreStore()
    mock_db = MagicMock()
    store._db = mock_db

    doc_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = doc_ref
    doc_ref.set.side_effect = [Aborted("conflict"), None]

    user = User(uid="u1", email="u@example.com", name="U")
    with patch("time.sleep"):
        store.save_run("run-004", {}, user)

    assert doc_ref.set.call_count == 2


def test_firestore_save_deadline_exceeded_retries():
    """save_run retries on DeadlineExceeded."""
    from google.api_core.exceptions import DeadlineExceeded
    from infra.auth import User
    from infra.firestore_store import FirestoreStore

    store = FirestoreStore()
    mock_db = MagicMock()
    store._db = mock_db

    doc_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = doc_ref
    doc_ref.set.side_effect = [DeadlineExceeded("slow"), None]

    user = User(uid="u1", email="u@example.com", name="U")
    with patch("time.sleep"):
        store.save_run("run-005", {}, user)

    assert doc_ref.set.call_count == 2
