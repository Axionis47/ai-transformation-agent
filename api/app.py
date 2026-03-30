import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import runs, ui
from api.routes.agents import router as agents_router
from api.routes.grounding import router as grounding_router
from api.routes.pitch import router as pitch_router
from api.routes.rag import router as rag_router
from api.routes.thought import router as thought_router

log = logging.getLogger(__name__)

app = FastAPI(title="AI Opportunity Mapper", version="0.1.0")


@app.on_event("startup")
def _init_storage() -> None:
    """Initialize storage backend from config at startup."""
    from core import run_manager
    from core.config import load_config

    cfg = load_config()
    backend = cfg.get("storage", {}).get("backend", "memory")

    if backend == "firestore":
        from services.storage.firestore_store import FirestoreStore

        project_id = cfg.get("gcp", {}).get("project_id")
        store = FirestoreStore(project_id=project_id)
        run_manager.init_storage(store)
        log.info("Storage: Firestore (project=%s)", project_id)
    else:
        log.info("Storage: in-memory")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs.router, prefix="/v1")
app.include_router(ui.router, prefix="/v1")
app.include_router(rag_router, prefix="/v1")
app.include_router(grounding_router, prefix="/v1")
app.include_router(thought_router, prefix="/v1")
app.include_router(pitch_router, prefix="/v1")
app.include_router(agents_router, prefix="/v1")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/v1/defaults")
def get_defaults() -> dict:
    """Return default config for the home page — no hardcoded frontend values."""
    from core.config import load_config

    cfg = load_config()
    budgets = cfg.get("budgets", {})
    models = cfg.get("models", {})
    return {
        "rag_budget": budgets.get("rag_query_budget", 15),
        "search_budget": budgets.get("external_search_query_budget", 25),
        "search_max_calls": budgets.get("external_search_max_calls", 8),
        "reasoning_model": models.get("reasoning_model", "gemini-2.5-flash"),
        "synthesis_model": models.get("synthesis_model", "gemini-2.5-pro"),
        "pipeline_stages": [
            "Intake",
            "Grounding",
            "Deep Research",
            "Hypothesis Formation",
            "Hypothesis Testing",
            "Synthesis",
            "Review",
        ],
    }
