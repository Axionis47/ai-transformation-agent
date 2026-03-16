"""Pipeline state — typed dataclass passed between agents."""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class PipelineState(BaseModel):
    """Working memory for a single pipeline run."""

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    url: str = ""
    dry_run: bool = False

    # Stage outputs — populated as pipeline progresses
    company_data: dict[str, Any] | None = None
    rag_context: list[dict[str, Any]] | None = None
    analysis: dict[str, Any] | None = None
    report: dict[str, Any] | None = None

    # Sprint 4 — new stage outputs
    signals: dict[str, Any] | None = None
    maturity: dict[str, Any] | None = None
    victory_matches: list[dict[str, Any]] | None = None
    use_cases: list[dict[str, Any]] | None = None

    # Metadata
    status: PipelineStatus = PipelineStatus.PENDING
    error: dict[str, Any] | None = None
    cost_usd: float = 0.0
    elapsed_seconds: float = 0.0
