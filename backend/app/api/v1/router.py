from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    config,
    dashboard,
    deletion_requests,
    internal,
    po_lines,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(po_lines.router)
api_router.include_router(deletion_requests.router)
api_router.include_router(dashboard.router)
api_router.include_router(config.router)
api_router.include_router(users.router)
api_router.include_router(internal.router)
