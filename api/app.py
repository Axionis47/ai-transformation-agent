from fastapi import FastAPI

from api.routes import runs, ui
from api.routes.grounding import router as grounding_router
from api.routes.pitch import router as pitch_router
from api.routes.rag import router as rag_router
from api.routes.thought import router as thought_router

app = FastAPI(title="AI Opportunity Mapper", version="0.1.0")

app.include_router(runs.router, prefix="/v1")
app.include_router(ui.router, prefix="/v1")
app.include_router(rag_router, prefix="/v1")
app.include_router(grounding_router, prefix="/v1")
app.include_router(thought_router, prefix="/v1")
app.include_router(pitch_router, prefix="/v1")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
