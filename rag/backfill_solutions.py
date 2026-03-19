"""Backfill victories.json with Sprint 8 fields (status, ingestion_date, etc.)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from rag.schemas import SolutionSchema

_VICTORIES = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "fixtures"
    / "rag_seeds"
    / "victories.json"
)

_TODAY = date.today().isoformat()

_ML_CATEGORY_MAP = {
    "regression": "predictive_model",
    "lstm": "predictive_model",
    "prophet": "predictive_model",
    "forecasting": "predictive_model",
    "classifier": "classification",
    "classification": "classification",
    "random forest": "classification",
    "gradient boost": "classification",
    "lightgbm": "classification",
    "xgboost": "classification",
    "bert": "nlp",
    "nlp": "nlp",
    "language": "nlp",
    "cnn": "computer_vision",
    "resnet": "computer_vision",
    "vision": "computer_vision",
    "constraint": "optimization",
    "scheduling": "optimization",
    "route": "optimization",
    "scoring model": "scoring_model",
    "weighted scoring": "scoring_model",
}


def _infer_category(ml_approach: str) -> str:
    lower = ml_approach.lower()
    for keyword, category in _ML_CATEGORY_MAP.items():
        if keyword in lower:
            return category
    return "predictive_model"


def backfill(path: Path = _VICTORIES) -> list[dict]:
    """Read victories, add missing Sprint 8 fields, validate, and return updated records."""
    records = json.loads(path.read_text())
    updated = []
    errors = []

    for r in records:
        r.setdefault("status", "active")
        r.setdefault("ingestion_date", _TODAY)
        r.setdefault("applicable_signals", [])
        ml_approach = r.get("tech_stack", {}).get("ml_approach", "")
        r.setdefault("solution_category", _infer_category(ml_approach))

        try:
            SolutionSchema(**r)
        except Exception as exc:
            errors.append(f"{r.get('id', '?')}: {exc}")
            continue

        updated.append(r)

    if errors:
        for msg in errors:
            print(f"VALIDATION ERROR: {msg}")
        raise SystemExit(1)

    return updated


def main() -> None:
    updated = backfill()
    _VICTORIES.write_text(json.dumps(updated, indent=2, ensure_ascii=False))
    print(f"{len(updated)} records backfilled and written to {_VICTORIES}")


if __name__ == "__main__":
    main()
