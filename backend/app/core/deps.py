"""
Shared FastAPI dependencies: who is making this request, and are they allowed
to do what they're asking. Every route that needs auth pulls from here, so
there's exactly one place that decides what a valid token/role looks like
(System Design §6).
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import TokenError, decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole

# tokenUrl is just used to populate the "Authorize" button in /docs — the
# actual verification happens in get_current_user below.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except TokenError as exc:
        raise credentials_error from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_error

    user = db.get(User, int(user_id))
    if user is None or not user.active:
        raise credentials_error
    return user


def require_roles(*roles: UserRole):
    """
    Dependency factory: `Depends(require_roles(UserRole.MANAGER, UserRole.ADMINISTRATOR))`
    raises 403 unless the current user has one of the given roles. Role checks
    live here, not scattered through business logic (System Design §6).
    """

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {[r.value for r in roles]}",
            )
        return current_user

    return _checker
