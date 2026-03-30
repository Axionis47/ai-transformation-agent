"""Evidence pruning utilities for loop boundaries and context assembly."""

from __future__ import annotations

from core.schemas import EvidenceItem


def prune_by_relevance(
    items: list[EvidenceItem],
    min_relevance: float = 0.3,
    max_items: int = 30,
) -> tuple[list[EvidenceItem], int]:
    """Remove items below threshold, cap at max_items. Returns (kept, dropped_count)."""
    filtered = [e for e in items if e.relevance_score >= min_relevance]
    filtered.sort(key=lambda e: e.relevance_score, reverse=True)
    dropped = len(items) - len(filtered[:max_items])
    return filtered[:max_items], dropped


def prune_for_field_scope(
    items: list[EvidenceItem],
    field_keywords: dict[str, list[str]],
    fields: list[str],
    max_per_field: int = 5,
) -> list[EvidenceItem]:
    """Keep only evidence relevant to specified fields, max per field."""
    if not fields:
        return items
    result_ids: set[str] = set()
    result: list[EvidenceItem] = []

    for field in fields:
        keywords = field_keywords.get(field, [])
        if not keywords:
            continue
        count = 0
        for item in items:
            if item.evidence_id in result_ids:
                continue
            text = (item.title + " " + item.snippet).lower()
            if any(kw in text for kw in keywords):
                result.append(item)
                result_ids.add(item.evidence_id)
                count += 1
                if count >= max_per_field:
                    break
    return result


def deduplicate_by_source(items: list[EvidenceItem]) -> list[EvidenceItem]:
    """Keep highest-scoring item per source_ref."""
    by_ref: dict[str, EvidenceItem] = {}
    for item in items:
        existing = by_ref.get(item.source_ref)
        if existing is None or item.relevance_score > existing.relevance_score:
            by_ref[item.source_ref] = item
    return sorted(by_ref.values(), key=lambda e: e.relevance_score, reverse=True)
