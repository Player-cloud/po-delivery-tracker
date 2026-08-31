from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.models.po_line import Priority, Status
from app.schemas.user import AssignableUser


class POLineBase(BaseModel):
    po_number: str
    po_line: int
    issue_date: date
    promised_delivery: date
    assigned_to_id: int  # required (PRD §14 Q2) — every PO line has an owner
    priority: Priority | None = None
    notes: str | None = None

    # NFR-7: validate server-side too, never trust the frontend alone.
    # `info` intentionally left untyped rather than importing pydantic's
    # ValidationInfo — the exact import path has moved between minor pydantic
    # versions, and info.data.get(...) works the same regardless of the type
    # hint. Confirm the pinned version in requirements.txt if you want the hint back.
    @field_validator("promised_delivery")
    @classmethod
    def promised_delivery_is_sane(cls, v: date, info) -> date:
        if v < date.today():
            raise ValueError("Promised Delivery date cannot be in the past")
        issue_date = info.data.get("issue_date")
        if issue_date and v < issue_date:
            raise ValueError("Promised Delivery date cannot be before Issue Date")
        return v


class POLineCreate(POLineBase):
    pass


class POLineUpdate(BaseModel):
    """All fields optional — this is a partial update (PUT with partial semantics).

    `assigned_to_id` may be *reassigned* but not *cleared*: it's a required field
    (PRD §14 Q2), so an explicit `null` is rejected here rather than hitting the
    database NOT NULL constraint.
    """

    issue_date: date | None = None
    promised_delivery: date | None = None
    delivered: bool | None = None
    assigned_to_id: int | None = None
    priority: Priority | None = None
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _reject_null_assignee(cls, data):
        if isinstance(data, dict) and "assigned_to_id" in data and data["assigned_to_id"] is None:
            raise ValueError(
                "assigned_to_id cannot be cleared — a PO line must always have an assignee"
            )
        return data


class POLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    po_number: str
    po_line: int
    issue_date: date
    promised_delivery: date
    delivered: bool
    priority: Priority | None
    notes: str | None

    # Computed, read-only — see app.models.po_line for why these aren't stored.
    lead_time_days: int | None
    days_remaining: int
    status: Status

    assigned_to_id: int | None
    assigned_to: AssignableUser | None = None
    created_by_id: int | None
    modified_by_id: int | None
    created_at: datetime
    modified_at: datetime
