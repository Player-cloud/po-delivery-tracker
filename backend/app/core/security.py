from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

_MAX_PASSWORD_BYTES = 72

_COMMON = {
    "password",
    "password1",
    "12345678",
    "123456789",
    "1234567890",
    "qwertyuiop",
    "changeme",
    "letmein",
    "administrator",
}


class WeakPasswordError(ValueError):
    """Password does not meet the policy — schema turns this into a 422."""


def validate_password_strength(password: str) -> None:
    if len(password) < settings.password_min_length:
        raise WeakPasswordError(
            f"Password must be at least {settings.password_min_length} characters"
        )
    if len(password.encode("utf-8")) > _MAX_PASSWORD_BYTES:
        raise WeakPasswordError(f"Password must be at most {_MAX_PASSWORD_BYTES} bytes")
    if len(set(password)) < 4:
        raise WeakPasswordError("Password is too repetitive")
    if password.lower() in _COMMON:
        raise WeakPasswordError("Password is too common")


def hash_password(password: str) -> str:
    validate_password_strength(password)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


class TokenError(Exception):
    """Raised for any invalid/expired JWT — callers turn this into a 401."""


def create_access_token(subject: str, role: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise TokenError(str(exc)) from exc
