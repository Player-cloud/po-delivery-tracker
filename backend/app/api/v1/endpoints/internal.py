"""
Internal, machine-only endpoints. No user session — these are called by the
infrastructure, not the browser.

`POST /internal/run-reminders` is the daily reminder pass (PRD §10, M1). It is
guarded by a shared secret rather than a JWT: the caller must send
`Authorization: Bearer <CRON_SECRET>`. In production that caller is a GitHub
Actions scheduled workflow; in dev it's a manual curl or `python -m
scripts.run_reminders`.
"""

import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.reminders import ReminderRunOut
from app.services.reminders import run_reminders

router = APIRouter(prefix="/internal", tags=["internal"])
settings = get_settings()

_BEARER_PREFIX = "Bearer "


def verify_cron_secret(authorization: str | None = Header(default=None)) -> None:
    """Constant-time check of the `Authorization: Bearer <CRON_SECRET>` header."""
    expected = settings.cron_secret
    provided = ""
    if authorization and authorization.startswith(_BEARER_PREFIX):
        provided = authorization[len(_BEARER_PREFIX) :]

    if not expected or not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing cron secret",
        )


@router.post(
    "/run-reminders",
    response_model=ReminderRunOut,
    dependencies=[Depends(verify_cron_secret)],
)
def trigger_reminder_run(db: Session = Depends(get_db)) -> ReminderRunOut:
    result = run_reminders(db)
    return ReminderRunOut.model_validate(result)
