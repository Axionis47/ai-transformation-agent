from __future__ import annotations

import json
from pathlib import Path

from services.rag.schemas import EngagementCase
from services.rag.store import RAGStore

_DEFAULT_SEED_PATH = (
    Path(__file__).parent.parent.parent / "data" / "wins_kb_seed" / "engagements.json"
)


def load_engagements(json_path: str | None = None) -> list[EngagementCase]:
    """Load and validate engagement records from JSON seed file."""
    path = Path(json_path) if json_path else _DEFAULT_SEED_PATH
    with open(path) as f:
        raw = json.load(f)
    return [EngagementCase.model_validate(r) for r in raw]


def build_document_text(engagement: EngagementCase) -> str:
    """Build rich document text for semantic search embedding.

    Includes generalizable applicability, discovery insights, lessons learned,
    and tags so retrieval works across industries and for abstract queries.
    """
    impact_str = "; ".join(f"{k}: {v}" for k, v in engagement.measured_impact.items())
    conditions_str = "; ".join(engagement.conditions_for_success)
    anti_str = "; ".join(engagement.anti_patterns)
    tags_str = ", ".join(engagement.tags)

    parts = [
        f"{engagement.title}.",
        f"Applicable to: {engagement.industry} companies and similar businesses with {engagement.workflow_area} challenges.",
    ]
    if engagement.generalized_for:
        parts.append(f"Also relevant for: {engagement.generalized_for}")
    parts.append(f"Problem pattern: {engagement.problem}")
    parts.append(f"Solution approach: {engagement.solution_shape}.")
    parts.append(f"Key results: {impact_str}.")
    if engagement.discovery_insight:
        parts.append(f"Discovery insight: {engagement.discovery_insight}")
    if engagement.lessons_learned:
        parts.append(f"Lessons learned: {'; '.join(engagement.lessons_learned[:2])}")
    if engagement.implementation_friction:
        parts.append(f"Implementation friction: {'; '.join(engagement.implementation_friction[:2])}")
    parts.append(f"Prerequisites: {conditions_str}.")
    parts.append(f"Watch out for: {anti_str}.")
    parts.append(f"Tags: {tags_str}.")

    return "\n".join(parts)


def ingest(store: RAGStore, engagements: list[EngagementCase]) -> int:
    """Embed and store all engagement records. Returns count ingested."""
    docs = []
    for eng in engagements:
        text = build_document_text(eng)
        metadata = {
            "engagement_id": eng.engagement_id,
            "title": eng.title,
            "industry": eng.industry,
            "company_size_band": eng.company_size_band,
            "workflow_area": eng.workflow_area,
            "solution_shape": eng.solution_shape,
            "timeline_weeks": eng.timeline_weeks,
            "tags": ",".join(eng.tags),
        }
        docs.append({"id": eng.engagement_id, "text": text, "metadata": metadata})
    return store.add_documents(docs)


def ensure_loaded(store: RAGStore, json_path: str | None = None) -> int:
    """Idempotent: ingest seed data only if collection is empty."""
    if store.count() > 0:
        return store.count()
    engagements = load_engagements(json_path)
    return ingest(store, engagements)
