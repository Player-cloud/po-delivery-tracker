"""
"Forgot password" tokens (see app.models.password_reset_token).

The raw token only ever exists in the emailed link; the database keeps its
SHA-256. Requesting a new link replaces any earlier one, and a successful reset
deletes every token the user has.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User

settings = get_settings()

# Don't mint a second link for the same user within this window — stops the
# form being used to spam someone's inbox (the per-IP limiter covers the rest).
_MIN_GAP = timedelta(seconds=60)


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _aware(dt: datetime) -> datetime:
    # SQLite hands back naive datetimes; Postgres hands back aware ones.
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def create_reset_token(db: Session, user: User) -> str | None:
    """Return a fresh raw token for `user`, or None if one was issued moments ago."""
    now = datetime.now(UTC)
    newest = db.scalar(
        select(PasswordResetToken.created_at)
        .where(PasswordResetToken.user_id == user.id)
        .order_by(PasswordResetToken.created_at.desc())
        .limit(1)
    )
    if newest is not None and now - _aware(newest) < _MIN_GAP:
        return None

    db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
    raw = secrets.token_urlsafe(32)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=_hash(raw),
            expires_at=now + timedelta(minutes=settings.password_reset_expire_minutes),
        )
    )
    db.commit()
    return raw


def reset_password(db: Session, raw_token: str, new_password: str) -> User | None:
    """Set `new_password` if `raw_token` is valid; None if it isn't (unknown,
    expired, or the account is disabled). Raises WeakPasswordError before the
    token is touched, so a weak password doesn't burn the link."""
    new_hash = hash_password(new_password)

    token = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == _hash(raw_token))
    )
    if token is None or _aware(token.expires_at) < datetime.now(UTC):
        return None
    user = db.get(User, token.user_id)
    if user is None or not user.active:
        return None

    user.password_hash = new_hash
    db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
    db.commit()
    return user
