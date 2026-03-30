"""Memory type definitions, recall contracts, and provenance tracking."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel

from core.schemas import Provenance  # canonical definition


class MemoryType(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    PROFILE = "profile"


class RecallRequest(BaseModel):
    run_id: str
    need: str  # "thought_loop" | "mid_assessment" | "pitch_synthesis" | "report_composition"
    memory_types: list[MemoryType] = []
    max_items: int = 20
    min_relevance: float = 0.3
    source_types: list[str] | None = None
    field_scope: list[str] | None = None
    include_provenance: bool = False


class RecallResult(BaseModel):
    items: list = []  # list[EvidenceItem] - avoid circular import
    dropped_count: int = 0
    total_available: int = 0
    relevance_range: tuple[float, float] = (0.0, 0.0)


class PromotionCandidate(BaseModel):
    evidence_id: str
    target_type: MemoryType
    provenance: Optional[Provenance] = None
    confidence: float = 0.0
    promoted: bool = False
    rejection_reason: Optional[str] = None
