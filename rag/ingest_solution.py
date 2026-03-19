"""CLI to ingest Tenex delivered solutions into the tenex_delivered ChromaDB collection."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from rag.schemas import SolutionSchema

_COLLECTION = "tenex_delivered"


def _build_embed_text(record: dict) -> str:
    """Generate embed_text from structured fields when absent or empty."""
    industry = record.get("industry", "Unknown")
    profile = record.get("company_profile", {})
    size_label = profile.get("size_label", "")
    employees = profile.get("size_employees", "")
    revenue = profile.get("annual_revenue_usd", "")
    geo = profile.get("geography", "")
    problem = record.get("problem_statement", "")
    solution = record.get("solution_summary", "")
    results = record.get("results", {})
    primary = results.get("primary_metric", {})
    period = results.get("measurement_period", "")
    metric_label = primary.get("label", "")
    metric_value = primary.get("value", "")
    approach = record.get("tech_stack", {}).get("ml_approach", "")

    return (
        f"{industry.capitalize()} -- {size_label} company, {employees} employees, "
        f"{revenue}, {geo}\n\n"
        f"Problem: {problem}\n\nSolution: {solution}\n\n"
        f"Approach: {approach}\n\n"
        f"Results: {metric_label}: {metric_value} ({period})."
    )


def _validate_record(raw: dict) -> SolutionSchema | list[str]:
    """Validate a raw dict against SolutionSchema. Returns model or list of error strings."""
    try:
        return SolutionSchema.model_validate(raw)
    except ValidationError as exc:
        errors = []
        for e in exc.errors():
            field = ".".join(str(f) for f in e["loc"])
            errors.append(f"  {raw.get('id', '?')}: field '{field}' — {e['msg']}")
        return errors


def _upsert_record(validated: SolutionSchema, dry_run: bool) -> None:
    """Upsert a validated record into the tenex_delivered collection."""
    raw = validated.model_dump()
    if not raw.get("embed_text"):
        raw["embed_text"] = _build_embed_text(raw)
    if not raw.get("ingestion_date"):
        raw["ingestion_date"] = date.today().isoformat()

    if dry_run:
        print(f"[dry-run] Would upsert: {raw['id']} — {raw['engagement_title']}")
        print(f"  industry: {raw['industry']}")
        print(f"  status: {raw['status']}")
        print(f"  solution_category: {raw['solution_category']}")
        print(f"  embed_text (first 120 chars): {raw['embed_text'][:120]}")
        return

    from rag.vector_store import ChromaStore

    store = ChromaStore(collection_name=_COLLECTION)
    store._init_chroma()
    store._collection.upsert(
        ids=[raw["id"]],
        documents=[raw["embed_text"]],
        metadatas=[{
            "industry": raw["industry"],
            "size_label": raw["company_profile"]["size_label"],
            "engagement_title": raw["engagement_title"],
            "solution_category": raw["solution_category"],
            "status": raw["status"],
            "ingestion_date": raw.get("ingestion_date", ""),
        }],
    )
    print(f"Upserted: {raw['id']} — {raw['engagement_title']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a delivered solution into the tenex_delivered ChromaDB collection."
    )
    parser.add_argument("--file", required=True, help="Path to JSON file (single record or array)")
    parser.add_argument("--dry-run", action="store_true", help="Validate and log without writing")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {path}: {exc}", file=sys.stderr)
        sys.exit(1)

    records = payload if isinstance(payload, list) else [payload]

    all_errors: list[str] = []
    validated_records: list[SolutionSchema] = []

    for raw in records:
        result = _validate_record(raw)
        if isinstance(result, list):
            all_errors.extend(result)
        else:
            validated_records.append(result)

    if all_errors:
        print("Validation failed — nothing written.", file=sys.stderr)
        for err in all_errors:
            print(err, file=sys.stderr)
        sys.exit(1)

    mode = "dry-run" if args.dry_run else "live"
    print(f"Validated {len(validated_records)} record(s). Mode: {mode}")

    for validated in validated_records:
        try:
            _upsert_record(validated, dry_run=args.dry_run)
        except Exception as exc:
            print(f"Store write error for {validated.id}: {exc}", file=sys.stderr)
            sys.exit(2)

    if not args.dry_run:
        print(f"Done. {len(validated_records)} record(s) upserted into '{_COLLECTION}'.")


if __name__ == "__main__":
    main()
