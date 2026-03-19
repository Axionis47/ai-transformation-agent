"""CLI to ingest industry case studies into the 'industry_cases' ChromaDB collection."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from pydantic import ValidationError

from rag.schemas import IndustryCaseStudySchema

_COLLECTION = "industry_cases"


def _generate_embed_text(r: dict) -> str:
    parts = [
        r.get("case_title", ""),
        r.get("industry", ""),
        r.get("ai_application", {}).get("problem_addressed", ""),
        r.get("ai_application", {}).get("solution_description", ""),
        r.get("reported_outcomes", {}).get("headline_metric", ""),
    ]
    return " ".join(p for p in parts if p).strip()


def _validate(raw: list[dict]) -> tuple[list[IndustryCaseStudySchema], list[str]]:
    valid, errors = [], []
    for item in raw:
        rid = item.get("id", "<unknown>")
        try:
            valid.append(IndustryCaseStudySchema(**item))
        except ValidationError as exc:
            for e in exc.errors():
                errors.append(f"{rid}: {'.'.join(str(x) for x in e['loc'])} — {e['msg']}")
    return valid, errors


def _upsert(records: list[IndustryCaseStudySchema]) -> int:
    import chromadb

    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./rag/store")
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    col = chromadb.PersistentClient(path=persist_dir).get_or_create_collection(_COLLECTION)
    try:
        col.upsert(
            ids=[r.id for r in records],
            documents=[r.embed_text for r in records],
            metadatas=[{"industry": r.industry, "company_name": r.company_profile.company_name,
                        "use_case_category": r.use_case_category, "status": r.status} for r in records],
        )
        return 0
    except Exception as exc:
        print(f"Store write error: {exc}", file=sys.stderr)
        return 2


def run(file_path: str, dry_run: bool) -> int:
    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {file_path}", file=sys.stderr)
        return 1

    raw = json.loads(path.read_text())
    if isinstance(raw, dict):
        raw = [raw]

    valid_records, errors = _validate(raw)
    if errors:
        for e in errors:
            print(f"Validation error: {e}", file=sys.stderr)
        return 1

    for r in valid_records:
        if not r.embed_text:
            r.embed_text = _generate_embed_text(r.model_dump())

    if dry_run:
        for r in valid_records:
            print(f"[dry-run] Would upsert {r.id}: {r.case_title} ({r.industry})")
        print(f"[dry-run] {len(valid_records)} record(s) validated — no writes made.")
        return 0

    code = _upsert(valid_records)
    if code == 0:
        for r in valid_records:
            print(f"Upserted {r.id}: {r.case_title}")
        print(f"Done. {len(valid_records)} record(s) written to '{_COLLECTION}'.")
    return code


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest industry cases into 'industry_cases' collection.")
    parser.add_argument("--file", required=True, help="Path to JSON file (single record or array).")
    parser.add_argument("--dry-run", action="store_true", help="Validate only — no store writes.")
    args = parser.parse_args()
    sys.exit(run(args.file, args.dry_run))


if __name__ == "__main__":
    main()
