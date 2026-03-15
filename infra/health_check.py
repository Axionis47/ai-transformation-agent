"""Health check endpoint for Cloud Run.

Cloud Run requires a /health endpoint that returns 200.
This module provides the health check route.

Usage in FastAPI:
    from infra.health_check import health_router
    app.include_router(health_router)
"""

from fastapi import APIRouter
from pydantic import BaseModel
import os

health_router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    model_provider: str


@health_router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for Cloud Run liveness probes."""
    return HealthResponse(
        status="healthy",
        version=os.getenv("SERVICE_VERSION", "0.0.0"),
        model_provider=os.getenv("MODEL_PROVIDER", "vertex")
    )
