"""Persist analysis results to Firestore — one document per run_id.

Optional: only active when FIRESTORE_ENABLED=true. All other environments
(local dev, dry-run, CI) skip persistence without error.
"""

from __future__ import annotations

import os
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
        """Save analysis result. Stores user_uid so ownership can be verified."""
        self._init()
        from google.cloud import firestore  # noqa: F811

        doc = {
            **data,
            "user_uid": user.uid,
            "user_email": user.email,
            "user_name": user.name,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
        self._db.collection(_COLLECTION).document(run_id).set(doc)

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
