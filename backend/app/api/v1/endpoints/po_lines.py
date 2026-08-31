from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.crud import po_line as po_line_crud
from app.crud.po_line import DuplicatePOLineError, InvalidAssigneeError
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.po_line import POLineCreate, POLineOut, POLineUpdate

router = APIRouter(prefix="/po-lines", tags=["po-lines"])


def _assert_staff_can_touch(po_line, current_user: User) -> None:
    """Staff may only read/edit lines assigned to them (see crud.po_line._visible_to)."""
    if current_user.role == UserRole.STAFF and po_line.assigned_to_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this PO line")


@router.get("", response_model=list[POLineOut])
def list_po_lines(
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return po_line_crud.list_po_lines(db, current_user, status_filter=status_filter, search=search)


@router.get("/{po_line_id}", response_model=POLineOut)
def get_po_line(
    po_line_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    po_line = po_line_crud.get_po_line(db, po_line_id)
    if po_line is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PO line not found")
    _assert_staff_can_touch(po_line, current_user)
    return po_line


@router.post("", response_model=POLineOut, status_code=status.HTTP_201_CREATED)
def create_po_line(
    data: POLineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMINISTRATOR)),
):
    try:
        return po_line_crud.create_po_line(db, data, current_user)
    except DuplicatePOLineError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidAssigneeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{po_line_id}", response_model=POLineOut)
def update_po_line(
    po_line_id: int,
    data: POLineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMINISTRATOR)),
):
    po_line = po_line_crud.get_po_line(db, po_line_id)
    if po_line is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PO line not found")
    _assert_staff_can_touch(po_line, current_user)
    try:
        return po_line_crud.update_po_line(db, po_line, data, current_user)
    except InvalidAssigneeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# NOTE: there is deliberately no DELETE /po-lines/{id} endpoint. Deletion now
# always goes through POST /po-lines/{id}/deletion-requests followed by an
# Administrator approving it (see app.api.v1.endpoints.deletion_requests) —
# this guarantees every deletion has a reason and a permanent audit record,
# with no code path that can delete a PO line without one.
