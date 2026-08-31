from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="REST API for the PO Delivery Tracking System (see docs/SYSTEM_DESIGN.md).",
    version="0.1.0",
)

# Next.js dev server by default; tighten this to the real frontend origin in prod .env.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Used by Docker/Azure App Service health probes — no auth required."""
    return {"status": "ok", "environment": settings.environment}
