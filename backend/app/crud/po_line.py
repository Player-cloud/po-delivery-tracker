"""
Data-access layer for PO lines. Route handlers (app.api.v1.endpoints.po_lines)
stay thin and just call into here — keeps business rules in one testable place.
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.purchase_order import get_or_create_by_number
from app.models.po_line import DeliveryStatus, POLine, Status
from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from app.models.user import User, UserRole
from app.schemas.po_line import POLineCreate, POLineUpdate


class DuplicatePOLineError(Exception):
    """Raised when (po_number, line no.) already exists — the route turns this into a 409."""


class InvalidAssigneeError(Exception):
    """Raised when assigned_to_id doesn't point to an existing, active user — route turns this into a 400."""


class ClosedPurchaseOrderError(Exception):
    """Raised when adding a line to a CLOSED / CANCELLED PO — route turns this into a 409."""


def _validate_assignee(db: Session, assigned_to_id: int) -> None:
    user = db.get(User, assigned_to_id)
    if user is None or not user.active:
        raise InvalidAssigneeError(f"assigned_to_id {assigned_to_id} is not an active user")


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
    *,
    delivery_status: str | None = None,
    priority: str | None = None,
    due_within: int | None = None,
    purchase_order_id: int | None = None,
) -> list[POLine]:
    stmt = select(POLine).join(POLine.purchase_order)
    stmt = _visible_to(stmt, current_user)

    if status_filter:
        stmt = stmt.where(POLine.status == status_filter)
    if search:
        stmt = stmt.where(PurchaseOrder.po_number.ilike(f"%{search}%"))
    if delivery_status:
        stmt = stmt.where(POLine.delivery_status == delivery_status)
    if priority:
        stmt = stmt.where(POLine.priority == priority)
    if purchase_order_id is not None:
        stmt = stmt.where(POLine.purchase_order_id == purchase_order_id)

    stmt = stmt.order_by(POLine.promised_delivery.asc())
    rows = list(db.scalars(stmt))

    if due_within is not None:
        # "Due in 1-30 days" dashboard drill-through — filtered on the computed
        # days_remaining in Python (same approach as dashboard_summary; the SQL
        # expression is Postgres-only). Open lines only.
        rows = [
            line
            for line in rows
            if line.delivery_status != DeliveryStatus.COMPLETE
            and 1 <= line.days_remaining <= due_within
        ]

    return rows


def _delivery_status_from_update(data: POLineUpdate) -> DeliveryStatus | None:
    """M8 field wins; fall back to the pre-M8 `delivered` boolean."""
    if data.delivery_status is not None:
        return data.delivery_status
    if data.delivered is not None:
        return DeliveryStatus.COMPLETE if data.delivered else DeliveryStatus.NOT_DELIVERED
    return None


def create_po_line(db: Session, data: POLineCreate, current_user: User) -> POLine:
    po = get_or_create_by_number(db, data.po_number, current_user)

    if po.status in (PurchaseOrderStatus.CLOSED, PurchaseOrderStatus.CANCELLED):
        raise ClosedPurchaseOrderError(
            f"PO {po.po_number} is {po.status.value} — reopen it before adding lines"
        )

    exists = db.scalar(
        select(POLine).where(POLine.purchase_order_id == po.id, POLine.po_line == data.po_line)
    )
    if exists:
        raise DuplicatePOLineError(f"PO {po.po_number} line {data.po_line} already exists")

    _validate_assignee(db, data.assigned_to_id)

    fields = data.model_dump(exclude={"po_number"})
    po_line = POLine(
        **fields,
        purchase_order_id=po.id,
        created_by_id=current_user.id,
        modified_by_id=current_user.id,
    )
    db.add(po_line)
    db.flush()
    db.refresh(po)
    po.recompute_status()
    db.commit()
    db.refresh(po_line)
    return po_line


def update_po_line(db: Session, po_line: POLine, data: POLineUpdate, current_user: User) -> POLine:
    updates = data.model_dump(exclude_unset=True, exclude={"delivered", "delivery_status"})
    if "assigned_to_id" in updates:
        _validate_assignee(db, updates["assigned_to_id"])
    for field, value in updates.items():
        setattr(po_line, field, value)

    new_delivery = _delivery_status_from_update(data)
    if new_delivery is not None:
        po_line.delivery_status = new_delivery

    po_line.modified_by_id = current_user.id
    db.flush()
    if po_line.purchase_order is not None:
        po_line.purchase_order.recompute_status()
    db.commit()
    db.refresh(po_line)
    return po_line


def delete_po_line(db: Session, po_line: POLine) -> None:
    po = po_line.purchase_order
    db.delete(po_line)
    db.flush()
    if po is not None:
        db.refresh(po)
        po.recompute_status()
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

    pos = _visible_purchase_orders(db, current_user)
    pos_delivered = sum(1 for p in pos if p.status == PurchaseOrderStatus.DELIVERED)
    pos_closed = sum(1 for p in pos if p.status == PurchaseOrderStatus.CLOSED)

    return {
        # pre-M8
        "total_open": len(open_lines),
        "due_today": sum(1 for l in open_lines if l.status == Status.DUE_TODAY),
        "due_this_week": sum(
            1 for l in open_lines if today <= l.promised_delivery <= week_from_now
        ),
        "due_soon": sum(1 for l in open_lines if 1 <= l.days_remaining <= 7),
        "later": sum(1 for l in open_lines if l.days_remaining > 7),
        "overdue": sum(1 for l in open_lines if l.status == Status.OVERDUE),
        "completed": sum(1 for l in lines if l.delivered),
        "high_priority": sum(
            1 for l in open_lines if l.priority is not None and l.priority.value == "high"
        ),
        # M8
        "total_pos": len(pos),
        "total_po_lines": len(lines),
        "pos_delivered": pos_delivered,
        "pos_closed": pos_closed,
        "due_1_30": sum(1 for l in open_lines if 1 <= l.days_remaining <= 30),
    }


def _visible_purchase_orders(db: Session, current_user: User) -> list[PurchaseOrder]:
    stmt = select(PurchaseOrder)
    if current_user.role == UserRole.STAFF:
        stmt = stmt.where(PurchaseOrder.lines.any(POLine.assigned_to_id == current_user.id))
    return list(db.scalars(stmt))


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
    attention = [l for l in lines if not l.delivered and l.days_remaining <= within_days]
    attention.sort(key=lambda l: l.days_remaining)
    return attention[:limit]
