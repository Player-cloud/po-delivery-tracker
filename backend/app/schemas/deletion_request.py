from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.deletion_request import DeletionRequestStatus
from app.schemas.user import UserOut


class DeletionRequestCreate(BaseModel):
    reason: str


class DeletionRequestReview(BaseModel):
    """Used for both approve and reject — the route determines which happens."""

    resolution_notes: str | None = None


class DeletionRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    po_line_id: int | None  # null once approved — the PO line no longer exists
    po_number: str
    po_line: int
    reason: str
    status: DeletionRequestStatus
    requested_by: UserOut
    reviewed_by: UserOut | None = None
    reviewed_at: datetime | None
    resolution_notes: str | None
    created_at: datetime
