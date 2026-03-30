from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import run_manager
from services.rag.ingest import ensure_loaded
from services.rag.retrieval import RAGQueryResult, RAGRetriever
from services.rag.store import get_rag_store

router = APIRouter()


class RAGQueryRequest(BaseModel):
    query: str


@router.post("/runs/{run_id}/rag:query", response_model=RAGQueryResult)
def rag_query(run_id: str, body: RAGQueryRequest) -> RAGQueryResult:
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    store = get_rag_store()
    ensure_loaded(store)

    retriever = RAGRetriever(store=store, config=run.config_snapshot)
    return retriever.query(body.query, run_id, run.budget_state)
