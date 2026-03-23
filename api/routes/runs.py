from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import run_manager
from core.schemas import CompanyIntake, Run, TraceEvent
from services.trace import get_events

router = APIRouter()


class CreateRunRequest(BaseModel):
    company_name: str
    industry: str


@router.post("/runs", response_model=Run, status_code=201)
def create_run(body: CreateRunRequest) -> Run:
    return run_manager.create_run(
        company_name=body.company_name,
        industry=body.industry,
    )


@router.get("/runs/{run_id}", response_model=Run)
def get_run(run_id: str) -> Run:
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return run


@router.put("/runs/{run_id}/company-intake", response_model=Run)
def update_intake(run_id: str, intake: CompanyIntake) -> Run:
    if run_manager.get_run(run_id) is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return run_manager.update_intake(run_id, intake)


@router.get("/runs/{run_id}/trace", response_model=list[TraceEvent])
def get_trace(run_id: str) -> list[TraceEvent]:
    if run_manager.get_run(run_id) is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return get_events(run_id)
