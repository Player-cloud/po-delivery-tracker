"""
Data-access layer for PO lines. Route handlers (app.api.v1.endpoints.po_lines)
stay thin and just call into here — keeps business rules in one testable place.
"""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.po_line import POLine, Status
from app.models.user import User, UserRole
from app.schemas.po_line import POLineCreate, POLineUpdate


class DuplicatePOLineError(Exception):
    """Raised when (po_number, po_line) already exists — the route turns this into a 409."""


class InvalidAssigneeError(Exception):
    """Raised when assigned_to_id doesn't point to an existing, active user — route turns this into a 400."""


def _validate_assignee(db: Session, assigned_to_id: int) -> None:
    user = db.get(User, assigned_to_id)
    if user is None or not user.active:
        raise InvalidAssigneeError(
            f"assigned_to_id {assigned_to_id} is not an active user"
        )


def get_po_line(db: Session, po_line_id: int) -> POLine | None:
    return db.get(POLine, po_line_id)


def _visible_to(stmt, current_user: User):
    """
    SRS Open Question #1, resolved with a default: Staff only sees PO lines
    assigned to them; Manager/Administrator/Viewer see everything. Flagged as
    a default in docs/SRS.md — revisit if the employer wants it the other way.
    """
    if current_user.role == UserRole.STAFF:
        return stmt.where(POLine.assigned_to_id == current_user.id)
    return stmt


def list_po_lines(
    db: Session,
    current_user: User,
    status_filter: str | None = None,
    search: str | None = None,
) -> list[POLine]:
    stmt = select(POLine)
    stmt = _visible_to(stmt, current_user)

    if status_filter:
        stmt = stmt.where(POLine.status == status_filter)
    if search:
        stmt = stmt.where(POLine.po_number.ilike(f"%{search}%"))

    stmt = stmt.order_by(POLine.promised_delivery.asc())
    return list(db.scalars(stmt))


def create_po_line(db: Session, data: POLineCreate, current_user: User) -> POLine:
    exists = db.scalar(
        select(POLine).where(POLine.po_number == data.po_number, POLine.po_line == data.po_line)
    )
    if exists:
        raise DuplicatePOLineError(f"PO {data.po_number} line {data.po_line} already exists")

    _validate_assignee(db, data.assigned_to_id)

    po_line = POLine(**data.model_dump(), created_by_id=current_user.id, modified_by_id=current_user.id)
    db.add(po_line)
    db.commit()
    db.refresh(po_line)
    return po_line


def update_po_line(db: Session, po_line: POLine, data: POLineUpdate, current_user: User) -> POLine:
    updates = data.model_dump(exclude_unset=True)
    if "assigned_to_id" in updates:
        _validate_assignee(db, updates["assigned_to_id"])
    for field, value in updates.items():
        setattr(po_line, field, value)
    po_line.modified_by_id = current_user.id
    db.commit()
    db.refresh(po_line)
    return po_line


def delete_po_line(db: Session, po_line: POLine) -> None:
    db.delete(po_line)
    db.commit()


def dashboard_summary(db: Session, current_user: User) -> dict:
    """
    Computed in Python over the visible rows rather than a single SQL
    aggregate, for readability — fine at the volumes in NFR-1 (up to ~5,000
    open lines). If that ever becomes a bottleneck, this is the function to
    rewrite as a GROUP BY query; nothing above it needs to change.
    """
    lines = list_po_lines(db, current_user)
    today = date.today()
    week_from_now = today + timedelta(days=7)

    open_lines = [l for l in lines if not l.delivered]

    return {
        "total_open": len(open_lines),
        "due_today": sum(1 for l in open_lines if l.status == Status.DUE_TODAY),
        "due_this_week": sum(1 for l in open_lines if today <= l.promised_delivery <= week_from_now),
        "due_soon": sum(1 for l in open_lines if 1 <= l.days_remaining <= 7),
        "later": sum(1 for l in open_lines if l.days_remaining > 7),
        "overdue": sum(1 for l in open_lines if l.status == Status.OVERDUE),
        "completed": sum(1 for l in lines if l.delivered),
        "high_priority": sum(1 for l in open_lines if l.priority is not None and l.priority.value == "high"),
    }


# Open lines within this many days of their promised date (or already past it)
# count as "needs attention" for the dashboard list (FR-16).
ATTENTION_WITHIN_DAYS = 7
ATTENTION_LIMIT = 50


def attention_lines(
    db: Session,
    current_user: User,
    *,
    within_days: int = ATTENTION_WITHIN_DAYS,
    limit: int = ATTENTION_LIMIT,
) -> list[POLine]:
    """The open PO lines that need attention now — overdue first, then soonest
    due — capped at `limit`. Same visibility rules as the list view.
    """
    lines = list_po_lines(db, current_user)
    attention = [
        l for l in lines if not l.delivered and l.days_remaining <= within_days
    ]
    attention.sort(key=lambda l: l.days_remaining)
    return attention[:limit]
