import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.core.security import create_access_token, verify_password
from app.crud import password_reset as reset_crud
from app.crud.user import get_user_by_email
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import ForgotPasswordRequest, MessageOut, ResetPasswordRequest, Token
from app.schemas.user import UserOut
from app.services.notifications import EmailMessage, get_notification_sender

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
logger = logging.getLogger("app.auth")

# Same reply whether or not the address belongs to an account, so the form can't
# be used to discover who has one.
_FORGOT_REPLY = "If that email belongs to an account, a password reset link is on its way."


@router.post("/login", response_model=Token)
@limiter.limit(settings.login_rate_limit or "10000/hour")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    # OAuth2PasswordRequestForm calls the field "username" — we treat it as email.
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )

    token = create_access_token(subject=str(user.id), role=user.role.value)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def _send_reset_email(to: str, first_name: str | None, raw_token: str) -> None:
    """Runs after the response is sent, so timing doesn't reveal whether the
    address exists. Failures are logged, never surfaced to the requester."""
    link = f"{settings.frontend_base_url.rstrip('/')}/reset-password?token={raw_token}"
    greeting = f"Hi {first_name},\n\n" if first_name else ""
    body = (
        f"{greeting}"
        "We received a request to reset your PO Tracker password.\n\n"
        "Choose a new password here (the link works once and expires in "
        f"{settings.password_reset_expire_minutes} minutes):\n{link}\n\n"
        "If you didn't ask for this, you can ignore this email - your password "
        "won't change.\n"
    )
    try:
        get_notification_sender().send(
            EmailMessage(to=to, subject="Reset your PO Tracker password", text_body=body)
        )
    except Exception:  # never let a mail failure leak to the caller
        logger.warning("password reset email could not be sent", exc_info=True)


@router.post("/forgot-password", response_model=MessageOut, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(settings.forgot_password_rate_limit or "10000/hour")
def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> MessageOut:
    user = get_user_by_email(db, data.email)
    if user is not None and user.active:
        raw = reset_crud.create_reset_token(db, user)
        if raw is not None:
            background.add_task(_send_reset_email, user.email, user.first_name, raw)
    return MessageOut(detail=_FORGOT_REPLY)


@router.post("/reset-password", response_model=MessageOut)
@limiter.limit(settings.login_rate_limit or "10000/hour")
def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageOut:
    if reset_crud.reset_password(db, data.token, data.password) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid or has expired. Request a new one.",
        )
    return MessageOut(detail="Password updated. You can now sign in.")
