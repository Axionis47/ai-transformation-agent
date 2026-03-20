"""FastAPI entry point — POST /v1/analyze + health check + GET /v1/trace."""

from __future__ import annotations

import asyncio
import json
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from infra.firestore_store import get_firestore_store
from infra.health_check import health_router
from orchestrator.pipeline import run_pipeline
from orchestrator.state import PipelineStatus
from rag.ingest import ensure_seeds_loaded

_LOG_DIR = Path("logs/runs")
_RUN_ID_RE = re.compile(r"^[a-zA-Z0-9\-]+$")
_API_KEY = os.getenv("API_KEY", "")  # empty = open access (dev/demo mode)


def _verify_api_key(request: Request) -> None:
    """Reject requests that don't carry the configured API key.

    When API_KEY env var is not set (or empty), every request is allowed
    so local dev and dry-run demos work without configuration.
    """
    if not _API_KEY:
        return
    key = request.headers.get("X-API-Key", "")
    if key != _API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks once; yield to serve requests; clean up on shutdown."""
    try:
        ensure_seeds_loaded()
    except Exception:
        pass  # ChromaDB unavailable — dry-run mode still works
    yield


app = FastAPI(title="AI Transformation Discovery Agent", version="0.1.0", lifespan=lifespan)

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
    user_hints: dict | None = None


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
    pitch_brief: dict[str, Any] | None = None
    readiness: dict[str, Any] | None = None
    suggested_questions: list[dict[str, Any]] | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    agent: str


class AnalyzeError(BaseModel):
    error: ErrorDetail


@app.get("/v1/results/{run_id}")
async def get_result(run_id: str) -> dict[str, Any]:
    """Retrieve a saved analysis result from Firestore by run_id."""
    store = get_firestore_store()
    if not store:
        raise HTTPException(status_code=404, detail="Persistence not enabled")
    result = store.get_run(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Run not found")
    return result


@app.get("/v1/runs")
async def list_runs(request: Request) -> dict[str, Any]:
    """List recent analysis runs for a user (identified by X-User-Email header)."""
    store = get_firestore_store()
    if not store:
        return {"runs": []}
    email = request.headers.get("X-User-Email", "anonymous")
    return {"runs": store.list_runs(email)}


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


@app.post("/v1/analyze", response_model=AnalyzeSuccess, dependencies=[Depends(_verify_api_key)])
async def analyze(request: AnalyzeRequest) -> AnalyzeSuccess:
    """Run the full AI transformation analysis pipeline."""
    state = await asyncio.to_thread(
        run_pipeline,
        url=request.url,
        dry_run=request.dry_run,
        user_hints=request.user_hints,
    )

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

    response = AnalyzeSuccess(
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
        pitch_brief=state.pitch_brief,
        readiness=state.readiness,
        suggested_questions=state.suggested_questions,
    )

    # Persist to Firestore (optional, non-blocking — never fails the request)
    store = get_firestore_store()
    if store:
        try:
            store.save_run(
                run_id=state.run_id,
                data=response.model_dump(),
                user_email=request.headers.get("X-User-Email"),
            )
        except Exception:
            pass

    return response
