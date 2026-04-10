from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.client_factory import build_gemini_client
from core import run_manager
from services.grounder.grounder import Grounder, GroundingResult

router = APIRouter()


class GroundingRequest(BaseModel):
    prompt: str


@router.post("/runs/{run_id}/ground", response_model=GroundingResult)
def ground(run_id: str, body: GroundingRequest) -> GroundingResult:
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    client = build_gemini_client(run.config_snapshot)
    grounder = Grounder(client=client, config=run.config_snapshot)
    return grounder.ground(body.prompt, run_id, run.budget_state)
