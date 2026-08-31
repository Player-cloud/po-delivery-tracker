from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.STAFF


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    role: UserRole | None = None
    active: bool | None = None
    password: str | None = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
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
