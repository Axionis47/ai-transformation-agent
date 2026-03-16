"""FastAPI entry point — POST /v1/analyze + health check + GET /v1/trace."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from infra.health_check import health_router
from orchestrator.pipeline import run_pipeline
from orchestrator.state import PipelineStatus

_LOG_DIR = Path("logs/runs")
_RUN_ID_RE = re.compile(r"^[a-zA-Z0-9\-]+$")

app = FastAPI(title="AI Transformation Discovery Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)


class AnalyzeRequest(BaseModel):
    url: str
    dry_run: bool = False


class AnalyzeSuccess(BaseModel):
    run_id: str
    status: str
    elapsed_seconds: float
    cost_usd: float
    report: dict[str, Any]
    analysis: dict[str, Any] | None = None
    rag_context: list[dict[str, Any]] | None = None
    signals: dict[str, Any] | None = None
    maturity: dict[str, Any] | None = None
    victory_matches: list[dict[str, Any]] | None = None
    use_cases: list[dict[str, Any]] | None = None
    pages_fetched: list[str] | None = None
    signal_count: int | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    agent: str


class AnalyzeError(BaseModel):
    error: ErrorDetail


@app.get("/v1/trace/{run_id}")
async def get_trace(run_id: str) -> dict[str, Any]:
    """Return all log entries for a pipeline run."""
    if not _RUN_ID_RE.match(run_id):
        raise HTTPException(status_code=400, detail="Invalid run_id format")
    log_path = _LOG_DIR / f"{run_id}.jsonl"
    if not log_path.exists():
        raise HTTPException(status_code=404, detail=f"No trace found for run_id: {run_id}")
    stages = []
    with open(log_path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    stages.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return {"run_id": run_id, "stages": stages}


@app.post("/v1/analyze", response_model=AnalyzeSuccess)
async def analyze(request: AnalyzeRequest) -> AnalyzeSuccess:
    """Run the full AI transformation analysis pipeline."""
    state = run_pipeline(url=request.url, dry_run=request.dry_run)

    if state.status == PipelineStatus.FAILED:
        err = state.error or {}
        status_code = 422 if err.get("code") == "SCRAPE_THIN" else 500
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": {
                    "error": {
                        "code": err.get("code", "UNKNOWN"),
                        "message": err.get("message", "Pipeline failed"),
                        "agent": err.get("agent", "unknown"),
                    }
                }
            },
        )

    return AnalyzeSuccess(
        run_id=state.run_id,
        status=state.status,
        elapsed_seconds=state.elapsed_seconds,
        cost_usd=state.cost_usd,
        report=state.report or {},
        analysis=state.analysis,
        rag_context=state.rag_context,
        signals=state.signals,
        maturity=state.maturity,
        victory_matches=state.victory_matches,
        use_cases=state.use_cases,
        pages_fetched=state.pages_fetched,
        signal_count=state.signal_count,
    )
