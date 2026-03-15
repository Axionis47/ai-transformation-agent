"""FastAPI entry point — POST /v1/analyze + health check."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from infra.health_check import health_router
from orchestrator.pipeline import run_pipeline
from orchestrator.state import PipelineStatus

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


class ErrorDetail(BaseModel):
    code: str
    message: str
    agent: str


class AnalyzeError(BaseModel):
    error: ErrorDetail


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
    )
