"""Data-access layer for purchase orders (M8, PRD §18)."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.po_line import POLine
from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from app.models.user import User, UserRole


class DuplicatePurchaseOrderError(Exception):
    """Raised when a PO with this number already exists — the route turns this into a 409."""


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


def create_purchase_order(db: Session, po_number: str, current_user: User) -> PurchaseOrder:
    if get_by_number(db, po_number) is not None:
        raise DuplicatePurchaseOrderError(f"PO {po_number} already exists")
    po = PurchaseOrder(
        po_number=po_number,
        status=PurchaseOrderStatus.OPEN,
        created_by_id=current_user.id,
        modified_by_id=current_user.id,
    )
    db.add(po)
    db.commit()
    db.refresh(po)
    return po


def _visible_to(stmt, current_user: User):
    """Staff see only POs that have a line assigned to them; everyone else sees all."""
    if current_user.role == UserRole.STAFF:
        return stmt.where(PurchaseOrder.lines.any(POLine.assigned_to_id == current_user.id))
    return stmt


def is_visible(po: PurchaseOrder, current_user: User) -> bool:
    if current_user.role != UserRole.STAFF:
        return True
    return any(line.assigned_to_id == current_user.id for line in po.lines)


def list_purchase_orders(
    db: Session, current_user: User, status_filter: str | None = None
) -> list[PurchaseOrder]:
    stmt = select(PurchaseOrder).options(selectinload(PurchaseOrder.lines))
    stmt = _visible_to(stmt, current_user)
    if status_filter:
        stmt = stmt.where(PurchaseOrder.status == status_filter)
    stmt = stmt.order_by(PurchaseOrder.created_at.desc())
    return list(db.scalars(stmt))


# Manual status transitions (PRD §18.3). OPEN/DELIVERED are otherwise managed by
# PurchaseOrder.recompute_status().
_ACTIONS: dict[str, tuple[set[PurchaseOrderStatus], PurchaseOrderStatus | None]] = {
    # action: (allowed-from states, fixed target — or None to recompute from lines)
    "close": ({PurchaseOrderStatus.DELIVERED}, PurchaseOrderStatus.CLOSED),
    "cancel": (
        {PurchaseOrderStatus.OPEN, PurchaseOrderStatus.DELIVERED},
        PurchaseOrderStatus.CANCELLED,
    ),
    "reopen": ({PurchaseOrderStatus.CLOSED, PurchaseOrderStatus.CANCELLED}, None),
}


def set_status(db: Session, po: PurchaseOrder, action: str, current_user: User) -> PurchaseOrder:
    if action not in _ACTIONS:
        raise InvalidStatusTransitionError(f"Unknown action {action!r}")
    allowed_from, target = _ACTIONS[action]
    if po.status not in allowed_from:
        raise InvalidStatusTransitionError(
            f"Cannot {action} a PO that is {po.status.value} "
            f"(allowed from: {', '.join(s.value for s in allowed_from)})"
        )
    if target is not None:
        po.status = target
    else:
        # reopen: force back into the auto-managed band, then let the lines decide
        po.status = PurchaseOrderStatus.OPEN
        po.recompute_status()
    po.modified_by_id = current_user.id
    db.commit()
    db.refresh(po)
    return po
