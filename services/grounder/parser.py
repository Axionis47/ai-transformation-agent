from __future__ import annotations

from urllib.parse import urlparse

from pydantic import BaseModel


class GroundingChunk(BaseModel):
    uri: str
    title: str
    domain: str  # extracted from uri


class GroundingSupport(BaseModel):
    segment_text: str
    chunk_indices: list[int]
    confidence_scores: list[float]


class ParsedGroundingMetadata(BaseModel):
    text: str
    chunks: list[GroundingChunk]
    supports: list[GroundingSupport]
    search_queries: list[str]
    search_query_count: int
    search_entry_point_html: str | None = None


def _extract_domain(uri: str) -> str:
    try:
        return urlparse(uri).netloc or uri
    except Exception:
        return uri


def parse_grounding_response(raw: dict) -> ParsedGroundingMetadata:
    """Parse raw grounding API response into typed objects."""
    text = raw.get("text", "")
    metadata = raw.get("grounding_metadata") or {}

    # Parse search queries
    search_queries: list[str] = metadata.get("web_search_queries") or []

    # Parse grounding chunks — skip malformed entries missing uri
    chunks: list[GroundingChunk] = []
    for chunk_raw in metadata.get("grounding_chunks") or []:
        web = chunk_raw.get("web") or {}
        uri = web.get("uri", "")
        if not uri:
            continue
        title = web.get("title", "")
        chunks.append(GroundingChunk(uri=uri, title=title, domain=_extract_domain(uri)))

    # Parse grounding supports
    supports: list[GroundingSupport] = []
    for sup_raw in metadata.get("grounding_supports") or []:
        segment = sup_raw.get("segment") or {}
        segment_text = segment.get("text", "")
        chunk_indices = sup_raw.get("grounding_chunk_indices") or []
        confidence_scores = sup_raw.get("confidence_scores") or []
        supports.append(
            GroundingSupport(
                segment_text=segment_text,
                chunk_indices=chunk_indices,
                confidence_scores=confidence_scores,
            )
        )

    # Parse search entry point HTML
    entry_point = metadata.get("search_entry_point") or {}
    search_entry_point_html: str | None = entry_point.get("rendered_content")

    return ParsedGroundingMetadata(
        text=text,
        chunks=chunks,
        supports=supports,
        search_queries=search_queries,
        search_query_count=len(search_queries),
        search_entry_point_html=search_entry_point_html,
    )
