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

# Allowed origins come from CORS_ORIGINS (comma-separated); defaults to the
# local Next.js dev server. Set it to the deployed frontend URL in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """No-auth health probe — used by Render's health check and the keep-warm ping."""
    return {"status": "ok", "environment": settings.environment}
