"""FastAPI entry point — v1 pipeline + v2 session-based analyst copilot."""

from __future__ import annotations

import asyncio
import json
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from infra.auth import User, get_current_user
from infra.firestore_store import get_firestore_store
from infra.health_check import health_router
from infra.rate_limiter import get_rate_limiter
from ops.logger import get_logger
from orchestrator.pipeline import run_pipeline
from orchestrator.reasoning_engine import process_turn
from orchestrator.session_schemas import SessionState
from orchestrator.state import PipelineStatus
from rag.ingest import ensure_seeds_loaded

_LOG_DIR = Path("logs/runs")
_RUN_ID_RE = re.compile(r"^[a-zA-Z0-9\-]+$")


def _auth(request: Request) -> User:
    """Resolve caller identity from Google OAuth Bearer token."""
    return get_current_user(request.headers.get("Authorization"))


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
    match_results: dict[str, Any] | None = None
    pages_fetched: list[str] | None = None
    signal_count: int | None = None
    has_user_hints: bool = False
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
async def get_result(run_id: str, user: User = Depends(_auth)) -> dict[str, Any]:
    """Retrieve a saved analysis result. Caller must own the run."""
    store = get_firestore_store()
    if not store:
        raise HTTPException(status_code=404, detail="Persistence not enabled")
    result = store.get_run(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Run not found")
    if result.get("user_uid") != user.uid:
        raise HTTPException(status_code=403, detail="Access denied")
    return result


@app.get("/v1/runs")
async def list_runs(user: User = Depends(_auth)) -> dict[str, Any]:
    """List recent analysis runs for the authenticated user."""
    store = get_firestore_store()
    if not store:
        return {"runs": []}
    return {"runs": store.list_runs(user.uid)}


@app.get("/v1/trace/{run_id}")
async def get_trace(run_id: str, user: User = Depends(_auth)) -> dict[str, Any]:
    """Return all log entries for a pipeline run. Checks GCS then local file."""
    if not _RUN_ID_RE.match(run_id):
        raise HTTPException(status_code=400, detail="Invalid run_id format")

    raw_text = await asyncio.to_thread(_read_trace, run_id)
    if raw_text is None:
        raise HTTPException(status_code=404, detail=f"No trace found for run_id: {run_id}")

    stages = []
    for line in raw_text.splitlines():
        line = line.strip()
        if line:
            try:
                stages.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return {"run_id": run_id, "stages": stages}


def _read_trace(run_id: str) -> str | None:
    """Read trace JSONL from GCS (if configured) or local file. Returns None if missing."""
    import os

    bucket_name = os.getenv("GCS_TRACE_BUCKET", "")
    if bucket_name:
        try:
            from google.cloud import storage  # noqa: PLC0415

            client = storage.Client()
            blob = client.bucket(bucket_name).blob(f"traces/{run_id}.jsonl")
            if blob.exists():
                return blob.download_as_text()
        except Exception:
            pass  # Fall through to local file

    log_path = _LOG_DIR / f"{run_id}.jsonl"
    if log_path.exists():
        return log_path.read_text()
    return None


@app.post("/v1/analyze", response_model=AnalyzeSuccess)
async def analyze(
    request: AnalyzeRequest,
    http_request: Request,
    user: User = Depends(_auth),
) -> AnalyzeSuccess:
    """Run the full AI transformation analysis pipeline."""
    limiter = get_rate_limiter()
    allowed, retry_after = limiter.check(user.uid)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={"error": "rate_limit_exceeded", "retry_after_seconds": retry_after},
        )

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
        match_results=state.match_results,
        pages_fetched=state.pages_fetched,
        signal_count=state.signal_count,
        has_user_hints=state.has_user_hints,
        pitch_brief=state.pitch_brief,
        readiness=state.readiness,
        suggested_questions=state.suggested_questions,
    )

    # Persist to Firestore — log failures but never fail the request
    store = get_firestore_store()
    if store:
        try:
            store.save_run(run_id=state.run_id, data=response.model_dump(), user=user)
        except Exception as exc:
            _logger = get_logger(state.run_id)
            _logger.log("FIRESTORE", "save_failed", error=str(exc))

    # Flush trace log to GCS if GCS_TRACE_BUCKET is configured (no-op otherwise)
    trace_logger = get_logger(state.run_id)
    await asyncio.to_thread(trace_logger.flush_to_gcs, state.run_id)

    return response


# ---------------------------------------------------------------------------
# v2 — Session-based Analyst Copilot
# ---------------------------------------------------------------------------

_sessions: dict[str, SessionState] = {}


class CreateSessionRequest(BaseModel):
    company_name: str = ""
    dry_run: bool = False


class TurnRequest(BaseModel):
    message: str


@app.post("/v2/session")
async def create_session(
    request: CreateSessionRequest,
    user: User = Depends(_auth),
) -> dict[str, Any]:
    """Create a new analyst copilot session."""
    state = SessionState(
        company_name=request.company_name,
        dry_run=request.dry_run,
    )
    _sessions[state.session_id] = state

    welcome = f"Session started for {request.company_name or 'a new prospect'}."
    welcome += " Tell me what you know about this company."
    return {"session_id": state.session_id, "system_message": welcome}


@app.post("/v2/session/{session_id}/turn")
async def session_turn(
    session_id: str,
    request: TurnRequest,
    user: User = Depends(_auth),
) -> dict[str, Any]:
    """Send an analyst message and get the system response."""
    state = _sessions.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    response = await asyncio.to_thread(process_turn, state, request.message)

    recs = state.recommendations.model_dump() if state.recommendations else None
    questions = [q.model_dump() for q in state.questions_pending]

    return {
        "system_message": response,
        "recommendations": recs,
        "questions": questions,
        "turn_count": len(state.turn_history),
    }


@app.post("/v2/session/{session_id}/pitch")
async def generate_pitch(
    session_id: str,
    user: User = Depends(_auth),
) -> dict[str, Any]:
    """Generate the final calibrated pitch document."""
    state = _sessions.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    pitch = await asyncio.to_thread(process_turn, state, "generate pitch")

    recs = state.recommendations
    return {
        "pitch": pitch,
        "easy_wins": [w.model_dump() for w in recs.easy_wins] if recs else [],
        "moderate_wins": [w.model_dump() for w in recs.moderate_wins] if recs else [],
        "ambitious": [w.model_dump() for w in recs.ambitious] if recs else [],
    }
