"""Baseline eval runner — dry-run pipeline per test company, score all outputs."""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from evals.judge_client import JudgeClient  # noqa: E402
from orchestrator.pipeline import run_pipeline  # noqa: E402

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

_RUBRICS = {
    k: str(REPO_ROOT / "evals" / "rubrics" / f"{k}.yaml")
    for k in ("tier_classification", "evidence_grounding", "roi_basis")
}
_TEST_COMPANIES = REPO_ROOT / "evals" / "test_companies.json"
_BASELINES = REPO_ROOT / "evals" / "baselines.json"
_SPRINT = "sprint_6"


def _uc_vars(uc: dict, mat: dict | None) -> dict:
    mat = mat or {}
    return {
        "tier": uc.get("tier", ""), "title": uc.get("title", ""),
        "description": uc.get("description", ""),
        "evidence_signal_ids": ", ".join(uc.get("evidence_signal_ids", [])),
        "signals_summary": uc.get("why_this_company", ""),
        "composite_score": mat.get("composite_score", 0.0),
        "composite_label": mat.get("composite_label", ""),
        "roi_estimate": uc.get("roi_estimate", ""), "roi_basis": uc.get("roi_basis", ""),
        "why_this_company": uc.get("why_this_company", ""),
        "victory_matches_summary": uc.get("rag_benchmark", ""),
    }


def _score_company(name: str, url: str, judge: JudgeClient) -> dict:
    try:
        state = run_pipeline(url=url, dry_run=True)
    except Exception as exc:
        logger.warning("Pipeline failed for %s: %s", name, exc)
        return {k: 0.0 for k in _RUBRICS}

    use_cases = getattr(state, "use_cases", None) or []
    maturity = getattr(state, "maturity", None)

    if not use_cases:
        return {k: 0.0 for k in _RUBRICS}

    buckets: dict[str, list[float]] = {k: [] for k in _RUBRICS}
    for uc in use_cases[:3]:
        ctx = _uc_vars(uc, maturity)
        for key, path in _RUBRICS.items():
            buckets[key].append(judge.score(path, ctx))

    return {k: round(sum(v) / len(v), 2) if v else 0.0 for k, v in buckets.items()}


def run_baseline() -> None:
    companies = json.loads(_TEST_COMPANIES.read_text())
    judge = JudgeClient()
    results = {}

    for c in companies:
        print(f"[ci_eval] Running {c['name']}...")
        results[c["name"]] = _score_company(c["name"], c["url"], judge)
        print(f"[ci_eval]   {results[c['name']]}")

    avgs = {k: round(sum(r[k] for r in results.values()) / len(results), 2) for k in _RUBRICS}
    entry: dict = {"run_date": str(date.today()), "companies": results, "averages": avgs}
    if not judge._available:
        entry["note"] = "GCP_PROJECT_ID not set — scores are 0.0 placeholders."

    existing = json.loads(_BASELINES.read_text()) if _BASELINES.exists() else {}
    existing[_SPRINT] = entry
    _BASELINES.write_text(json.dumps(existing, indent=2))
    print(f"[ci_eval] Done. Averages: {avgs}")


if __name__ == "__main__":
    run_baseline()
