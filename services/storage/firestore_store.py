"""Firestore storage backend — persists runs across restarts and deployments.

Each run is stored as a Firestore document in the 'runs' collection.
The full Run object is serialized to JSON via Pydantic's model_dump().
Firestore handles sub-documents natively (evidence, hypotheses, etc.
are nested within the run document).

For runs with very large evidence sets (>200 items), evidence is
stored in a sub-collection to stay under the 1MB doc limit.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from google.cloud import firestore

from core.schemas import Run

log = logging.getLogger(__name__)

COLLECTION = "runs"
EVIDENCE_THRESHOLD = 150  # split evidence to sub-collection above this count


class FirestoreStore:
    """Firestore-backed run persistence."""

    def __init__(self, project_id: str | None = None) -> None:
        self._db = firestore.Client(project=project_id)
        self._collection = self._db.collection(COLLECTION)
        log.info("FirestoreStore initialized (project=%s)", project_id or "default")

    def save_run(self, run: Run) -> None:
        data = run.model_dump(mode="json")

        # Split large evidence to sub-collection
        evidence = data.pop("evidence", [])
        data["evidence_count"] = len(evidence)

        if len(evidence) > EVIDENCE_THRESHOLD:
            data["evidence_split"] = True
            self._save_evidence_subcollection(run.run_id, evidence)
        else:
            data["evidence_split"] = False
            data["evidence"] = evidence

        self._collection.document(run.run_id).set(data)

    def get_run(self, run_id: str) -> Run | None:
        doc = self._collection.document(run_id).get()
        if not doc.exists:
            return None

        data = doc.to_dict()
        if not data:
            return None

        # Reassemble split evidence
        if data.get("evidence_split"):
            data["evidence"] = self._load_evidence_subcollection(run_id)
        data.pop("evidence_count", None)
        data.pop("evidence_split", None)

        return Run.model_validate(data)

    def list_runs(self, limit: int = 50, offset: int = 0) -> list[Run]:
        query = (
            self._collection
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit + offset)
        )
        docs = list(query.stream())
        runs = []
        for doc in docs[offset:]:
            data = doc.to_dict()
            if not data:
                continue
            # Don't load full evidence for list view
            if data.get("evidence_split"):
                data["evidence"] = []
            data.pop("evidence_count", None)
            data.pop("evidence_split", None)
            try:
                runs.append(Run.model_validate(data))
            except Exception as e:
                log.warning("Skipping malformed run %s: %s", doc.id, e)
        return runs

    def delete_run(self, run_id: str) -> bool:
        doc_ref = self._collection.document(run_id)
        if not doc_ref.get().exists:
            return False
        # Delete evidence sub-collection first
        self._delete_subcollection(doc_ref.collection("evidence"))
        doc_ref.delete()
        return True

    # --- Evidence sub-collection ---

    def _save_evidence_subcollection(self, run_id: str, evidence: list[dict]) -> None:
        coll = self._collection.document(run_id).collection("evidence")
        batch = self._db.batch()
        for i, ev in enumerate(evidence):
            eid = ev.get("evidence_id", str(i))
            batch.set(coll.document(eid), ev)
            if (i + 1) % 450 == 0:  # Firestore batch limit is 500
                batch.commit()
                batch = self._db.batch()
        batch.commit()

    def _load_evidence_subcollection(self, run_id: str) -> list[dict]:
        coll = self._collection.document(run_id).collection("evidence")
        return [doc.to_dict() for doc in coll.stream() if doc.to_dict()]

    def _delete_subcollection(self, coll_ref: firestore.CollectionReference) -> None:
        docs = list(coll_ref.limit(500).stream())
        while docs:
            batch = self._db.batch()
            for doc in docs:
                batch.delete(doc.reference)
            batch.commit()
            docs = list(coll_ref.limit(500).stream())
