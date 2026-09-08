from fastapi import APIRouter

from app.api.v1.endpoints import (
    attachments,
    auth,
    config,
    dashboard,
    deletion_requests,
    internal,
    po_lines,
    purchase_orders,
    reports,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(purchase_orders.router)
api_router.include_router(po_lines.router)
api_router.include_router(reports.router)
api_router.include_router(attachments.router)
api_router.include_router(deletion_requests.router)
api_router.include_router(dashboard.router)
api_router.include_router(config.router)
api_router.include_router(users.router)
api_router.include_router(internal.router)
