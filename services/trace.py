from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from core.events import EventType
from core.schemas import TraceEvent

_LOGS_DIR = Path(__file__).parent.parent / "logs"

# In-memory store: run_id -> list of TraceEvent
_events: dict[str, list[TraceEvent]] = {}


def emit(run_id: str, event_type: EventType, payload: dict | None = None) -> TraceEvent:
    """Create a TraceEvent, persist to JSONL, store in memory, and return it."""
    _LOGS_DIR.mkdir(exist_ok=True)

    event = TraceEvent(
        event_id=str(uuid.uuid4()),
        run_id=run_id,
        timestamp=datetime.now(timezone.utc),
        event_type=event_type.value,
        payload=payload or {},
    )

    log_path = _LOGS_DIR / f"{run_id}.jsonl"
    with open(log_path, "a") as f:
        f.write(event.model_dump_json() + "\n")

    _events.setdefault(run_id, []).append(event)
    return event


def get_events(run_id: str) -> list[TraceEvent]:
    """Return all in-memory trace events for a run."""
    return _events.get(run_id, [])
