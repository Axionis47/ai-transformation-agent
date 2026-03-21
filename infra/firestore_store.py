"""Persist analysis results to Firestore — one document per run_id.

Optional: only active when FIRESTORE_ENABLED=true. All other environments
(local dev, dry-run, CI) skip persistence without error.
"""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from infra.auth import User

_PROJECT = os.getenv("GCP_PROJECT_ID", "plotpointe")
_COLLECTION = "analysis_runs"


class FirestoreStore:
    """Thin wrapper around Firestore for analysis result persistence."""

    def __init__(self) -> None:
        self._db: Any = None

    def _init(self) -> None:
        if self._db is not None:
            return
        from google.cloud import firestore  # deferred import — optional dep

        self._db = firestore.Client(project=_PROJECT)

    def save_run(self, run_id: str, data: dict, user: "User") -> None:
        """Save analysis result with retry on transient errors.

        Retries up to 3 times (backoff: 0.5s, 1s, 2s) for transient errors:
        ServiceUnavailable, Aborted, DeadlineExceeded.

        Raises the final exception after all retries are exhausted — the
        caller (app.py) logs the failure but does not fail the HTTP response.
        """
        self._init()
        from google.cloud import firestore  # noqa: F811
        from google.api_core.exceptions import (  # noqa: PLC0415
            Aborted,
            DeadlineExceeded,
            ServiceUnavailable,
        )

        _TRANSIENT = (ServiceUnavailable, Aborted, DeadlineExceeded)
        _BACKOFFS = (0.5, 1.0, 2.0)

        doc = {
            **data,
            "user_uid": user.uid,
            "user_email": user.email,
            "user_name": user.name,
            "created_at": firestore.SERVER_TIMESTAMP,
        }

        last_exc: Exception | None = None
        for attempt, backoff in enumerate(_BACKOFFS, start=1):
            try:
                self._db.collection(_COLLECTION).document(run_id).set(doc)
                return
            except _TRANSIENT as exc:
                last_exc = exc
                if attempt < len(_BACKOFFS):
                    time.sleep(backoff)
            except Exception:
                raise  # Non-transient: PermissionDenied, NotFound, etc.

        raise last_exc  # type: ignore[misc]

    def get_run(self, run_id: str) -> dict | None:
        """Retrieve analysis result by run_id. Returns None if not found.

        Caller is responsible for checking user_uid before returning data.
        """
        self._init()
        doc = self._db.collection(_COLLECTION).document(run_id).get()
        return doc.to_dict() if doc.exists else None

    def list_runs(self, user_uid: str, limit: int = 20) -> list[dict]:
        """List recent runs owned by user_uid, newest first."""
        self._init()
        from google.cloud import firestore  # noqa: F811

        docs = (
            self._db.collection(_COLLECTION)
            .where("user_uid", "==", user_uid)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        return [{"run_id": d.id, **d.to_dict()} for d in docs]


def get_firestore_store() -> FirestoreStore | None:
    """Factory. Returns None when Firestore is not configured.

    Set FIRESTORE_ENABLED=true to activate. When unset or false the
    persistence layer is skipped entirely — local dev and dry-run are
    unaffected.
    """
    enabled = os.getenv("FIRESTORE_ENABLED", "").lower()
    if enabled in ("true", "1", "yes"):
        return FirestoreStore()
    return None
