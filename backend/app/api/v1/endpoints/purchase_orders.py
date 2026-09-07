from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.crud import purchase_order as po_crud
from app.crud.purchase_order import (
    DuplicatePurchaseOrderError,
    InvalidStatusTransitionError,
)
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.purchase_order import (
    PurchaseOrderAction,
    PurchaseOrderCreate,
    PurchaseOrderDetail,
    PurchaseOrderOut,
)

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


@router.get("", response_model=list[PurchaseOrderOut])
def list_purchase_orders(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return po_crud.list_purchase_orders(db, current_user, status_filter=status_filter)


@router.get("/{po_id}", response_model=PurchaseOrderDetail)
def get_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    po = po_crud.get_purchase_order(db, po_id)
    if po is None or not po_crud.is_visible(po, current_user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found"
        )
    return po


@router.post("", response_model=PurchaseOrderOut, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMINISTRATOR)
    ),
):
    try:
        return po_crud.create_purchase_order(db, data.po_number, current_user)
    except DuplicatePurchaseOrderError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.put("/{po_id}", response_model=PurchaseOrderDetail)
def change_purchase_order_status(
    po_id: int,
    data: PurchaseOrderAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.MANAGER, UserRole.ADMINISTRATOR)),
):
    """Close / cancel / reopen a PO (PRD §18.3). Managers and administrators only."""
    po = po_crud.get_purchase_order(db, po_id)
    if po is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found"
        )
    try:
        return po_crud.set_status(db, po, data.action, current_user)
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
