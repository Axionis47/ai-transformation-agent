from __future__ import annotations

import json
from pathlib import Path

from services.rag.schemas import ChunkType, EngagementCase
from services.rag.store import RAGStore

_DEFAULT_SEED_PATH = Path(__file__).parent.parent.parent / "data" / "wins_kb_seed" / "engagements.json"


def load_engagements(json_path: str | None = None) -> list[EngagementCase]:
    """Load and validate engagement records from JSON seed file."""
    path = Path(json_path) if json_path else _DEFAULT_SEED_PATH
    with open(path) as f:
        raw = json.load(f)
    return [EngagementCase.model_validate(r) for r in raw]


# ---------------------------------------------------------------------------
# Chunk builders — one per ChunkType
# Each returns self-contained prose optimised for embedding similarity.
# ---------------------------------------------------------------------------


def _build_problem_pattern(e: EngagementCase) -> str:
    metrics = "; ".join(f"{k}: {v}" for k, v in e.baseline_metrics.items())
    lines = [
        f"{e.title}. {e.industry.replace('_', ' ').title()} company, {e.company_size_band} employees.",
        f"Workflow area: {e.workflow_area}.",
        f"Problem: {e.problem}",
    ]
    if metrics:
        lines.append(f"Baseline metrics: {metrics}.")
    return "\n".join(lines)


def _build_solution_approach(e: EngagementCase) -> str:
    stack = ", ".join(e.tech_stack)
    lines = [
        f"{e.title}. Solution type: {e.solution_shape} for {e.workflow_area} in {e.industry.replace('_', ' ')}.",
    ]
    if e.solution_description:
        lines.append(f"What was built: {e.solution_description}")
    lines.append(f"Tech stack used: {stack}.")
    if e.team_composition:
        lines.append(f"Team: {e.team_composition}.")
    cost_line = f"Delivered in {e.timeline_weeks} weeks for a {e.company_size_band} employee company"
    if e.engagement_value_usd:
        cost_line += f" at ${e.engagement_value_usd:,} engagement value"
    lines.append(cost_line + ".")
    return "\n".join(lines)


def _build_preconditions(e: EngagementCase) -> str:
    conds = "\n".join(f"- {c}" for c in e.conditions_for_success)
    antis = "\n".join(f"- {a}" for a in e.anti_patterns)
    return "\n".join(
        [
            f"{e.title}. Prerequisites for success:",
            conds,
            "Anti-patterns — do NOT pursue if:",
            antis,
        ]
    )


def _build_outcomes(e: EngagementCase) -> str:
    impact = "\n".join(f"- {k}: {v}" for k, v in e.measured_impact.items())
    drivers = ", ".join(e.roi_drivers)
    lines = [
        f"{e.title}. {e.industry.replace('_', ' ').title()}, {e.company_size_band} employees.",
    ]
    if e.outcome_narrative:
        lines.append(e.outcome_narrative)
    if e.baseline_metrics:
        baseline = "; ".join(f"{k}: {v}" for k, v in e.baseline_metrics.items())
        lines.append(f"Before: {baseline}.")
    lines.append("After implementation:")
    lines.append(impact)
    lines.append(f"ROI was driven by: {drivers}.")
    return "\n".join(lines)


def _build_discovery_insight(e: EngagementCase) -> str:
    lines = [f"{e.title}."]
    if e.discovery_insight:
        lines.append(f"Discovery: {e.discovery_insight}")
    if e.lessons_learned:
        lines.append("Key lessons:")
        for lesson in e.lessons_learned[:3]:
            lines.append(f"- {lesson}")
    return "\n".join(lines)


def _build_implementation_friction(e: EngagementCase) -> str:
    lines = [
        f"{e.title}. {e.industry.replace('_', ' ').title()}, {e.solution_shape}, {e.timeline_weeks} weeks planned.",
        "What caused friction:",
    ]
    for f_item in e.implementation_friction:
        lines.append(f"- {f_item}")
    return "\n".join(lines)


def _build_generalization(e: EngagementCase) -> str:
    tags_text = ", ".join(e.tags)
    lines = [
        f"{e.title}. Originally delivered for {e.industry.replace('_', ' ')} ({e.workflow_area}).",
    ]
    if e.generalized_for:
        lines.append(f"Generalizes to: {e.generalized_for}")
    if e.buyer_persona:
        lines.append(f"Buyer persona: {e.buyer_persona}")
    if e.trigger_event:
        lines.append(f"Typical trigger: {e.trigger_event}")
    lines.append(f"Related areas: {tags_text}.")
    lines.append(f"Solution shape: {e.solution_shape}.")
    return "\n".join(lines)


_CHUNK_BUILDERS = {
    ChunkType.PROBLEM_PATTERN: _build_problem_pattern,
    ChunkType.SOLUTION_APPROACH: _build_solution_approach,
    ChunkType.PRECONDITIONS: _build_preconditions,
    ChunkType.OUTCOMES: _build_outcomes,
    ChunkType.DISCOVERY_INSIGHT: _build_discovery_insight,
    ChunkType.IMPLEMENTATION_FRICTION: _build_implementation_friction,
    ChunkType.GENERALIZATION: _build_generalization,
}


# ---------------------------------------------------------------------------
# Shared metadata builder
# ---------------------------------------------------------------------------


def _build_metadata(e: EngagementCase, chunk_type: ChunkType) -> dict:
    return {
        "engagement_id": e.engagement_id,
        "chunk_type": chunk_type.value,
        "title": e.title,
        "industry": e.industry,
        "company_size_band": e.company_size_band,
        "workflow_area": e.workflow_area,
        "solution_shape": e.solution_shape,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_chunks(engagement: EngagementCase) -> list[dict]:
    """Split one engagement into 7 independently retrievable chunks.

    Returns list of {"id": str, "text": str, "metadata": dict}.
    """
    chunks = []
    for chunk_type, builder in _CHUNK_BUILDERS.items():
        doc_id = f"{engagement.engagement_id}::{chunk_type.value}"
        text = builder(engagement)
        metadata = _build_metadata(engagement, chunk_type)
        chunks.append({"id": doc_id, "text": text, "metadata": metadata})
    return chunks


def ingest(store: RAGStore, engagements: list[EngagementCase]) -> int:
    """Embed and store all engagement chunks. Returns count ingested."""
    all_docs = []
    for eng in engagements:
        all_docs.extend(build_chunks(eng))
    return store.add_documents(all_docs)


def ensure_loaded(store: RAGStore, json_path: str | None = None) -> int:
    """Idempotent: ingest seed data only if collection is empty."""
    if store.count() > 0:
        return store.count()
    engagements = load_engagements(json_path)
    return ingest(store, engagements)
