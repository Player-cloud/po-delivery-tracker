from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.core.security import validate_password_strength
from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.STAFF


class UserCreate(UserBase):
    password: str
    # Collected on the create form (M8). Optional at the API for back-compat
    # with pre-M8 clients; the frontend form requires it.
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def _strong(cls, v: str) -> str:
        validate_password_strength(v)
        return v


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    active: bool | None = None
    password: str | None = None

    @field_validator("password")
    @classmethod
    def _strong(cls, v: str | None) -> str | None:
        if v is not None:
            validate_password_strength(v)
        return v


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str | None = None
    active: bool
    created_at: datetime


class AssignableUser(BaseModel):
    """Minimal user info for populating an 'Assigned To' picker — no role/status.

    `email` is a plain str here (it was already validated as EmailStr on user
    creation) so this output schema never rejects a stored address.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str | None = None
    display_name: str  # full name if set, else email (model property)
