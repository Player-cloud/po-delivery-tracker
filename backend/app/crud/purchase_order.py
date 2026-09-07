"""Data-access layer for purchase orders (M8, PRD §18)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.po_line import POLine
from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from app.models.user import User, UserRole


class InvalidStatusTransitionError(Exception):
    """Raised when a manual PO status change isn't allowed from the current state."""


def get_purchase_order(db: Session, po_id: int) -> PurchaseOrder | None:
    return db.get(PurchaseOrder, po_id)


def get_by_number(db: Session, po_number: str) -> PurchaseOrder | None:
    return db.scalar(select(PurchaseOrder).where(PurchaseOrder.po_number == po_number))


def get_or_create_by_number(
    db: Session, po_number: str, current_user: User | None = None
) -> PurchaseOrder:
    """Find the PO with this number, or create a fresh OPEN one. Does not commit —
    the caller's transaction does."""
    po = get_by_number(db, po_number)
    if po is not None:
        return po
    uid = current_user.id if current_user is not None else None
    po = PurchaseOrder(
        po_number=po_number,
        status=PurchaseOrderStatus.OPEN,
        created_by_id=uid,
        modified_by_id=uid,
    )
    db.add(po)
    db.flush()  # assign po.id without ending the transaction
    return po


def _visible_to(stmt, current_user: User):
    """Staff see only POs that have a line assigned to them; everyone else sees all."""
    if current_user.role == UserRole.STAFF:
        return stmt.where(PurchaseOrder.lines.any(POLine.assigned_to_id == current_user.id))
    return stmt


def list_purchase_orders(
    db: Session, current_user: User, status_filter: str | None = None
) -> list[PurchaseOrder]:
    stmt = select(PurchaseOrder).options(selectinload(PurchaseOrder.lines))
    stmt = _visible_to(stmt, current_user)
    if status_filter:
        stmt = stmt.where(PurchaseOrder.status == status_filter)
    stmt = stmt.order_by(PurchaseOrder.created_at.desc())
    return list(db.scalars(stmt))


def count_by_status(db: Session, current_user: User) -> dict[PurchaseOrderStatus, int]:
    stmt = select(PurchaseOrder.status, func.count()).group_by(PurchaseOrder.status)
    stmt = _visible_to(stmt, current_user)
    return dict(db.execute(stmt).all())


def total_pos(db: Session, current_user: User) -> int:
    stmt = _visible_to(select(func.count()).select_from(PurchaseOrder), current_user)
    return db.scalar(stmt) or 0
