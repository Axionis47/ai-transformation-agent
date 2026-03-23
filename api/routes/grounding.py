from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import run_manager
from services.grounder.fake_client import FakeGeminiClient
from services.grounder.grounder import Grounder, GroundingResult

router = APIRouter()


class GroundingRequest(BaseModel):
    prompt: str


@router.post("/runs/{run_id}/ground", response_model=GroundingResult)
def ground(run_id: str, body: GroundingRequest) -> GroundingResult:
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    client: object
    try:
        from services.grounder.client import GeminiClient
        client = GeminiClient(config=run.config_snapshot)
    except Exception:
        client = FakeGeminiClient()

    grounder = Grounder(client=client, config=run.config_snapshot)
    return grounder.ground(body.prompt, run_id, run.budget_state)
