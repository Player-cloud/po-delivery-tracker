from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.crud import deletion_request as dr_crud
from app.crud import po_line as po_line_crud
from app.crud.deletion_request import DuplicatePendingRequestError, InvalidStatusTransitionError
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.deletion_request import DeletionRequestCreate, DeletionRequestOut, DeletionRequestReview

router = APIRouter(tags=["deletion-requests"])


@router.post(
    "/po-lines/{po_line_id}/deletion-requests",
    response_model=DeletionRequestOut,
    status_code=status.HTTP_201_CREATED,
)
def request_deletion(
    po_line_id: int,
    data: DeletionRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Any authenticated user who can see this PO line can request its deletion —
    Staff/Manager/Administrator alike. Only an Administrator can actually approve it."""
    po_line = po_line_crud.get_po_line(db, po_line_id)
    if po_line is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PO line not found")
    if current_user.role == UserRole.STAFF and po_line.assigned_to_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this PO line")

    try:
        return dr_crud.create_deletion_request(db, po_line, data.reason, current_user)
    except DuplicatePendingRequestError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/deletion-requests", response_model=list[DeletionRequestOut])
def list_deletion_requests(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    return dr_crud.list_deletion_requests(db, status_filter=status_filter)


@router.post("/deletion-requests/{request_id}/approve", response_model=DeletionRequestOut)
def approve_deletion_request(
    request_id: int,
    data: DeletionRequestReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    request = dr_crud.get_deletion_request(db, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deletion request not found")
    try:
        return dr_crud.approve_deletion_request(db, request, current_user, data.resolution_notes)
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/deletion-requests/{request_id}/reject", response_model=DeletionRequestOut)
def reject_deletion_request(
    request_id: int,
    data: DeletionRequestReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    request = dr_crud.get_deletion_request(db, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deletion request not found")
    try:
        return dr_crud.reject_deletion_request(db, request, current_user, data.resolution_notes)
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
