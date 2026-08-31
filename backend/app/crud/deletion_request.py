from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.po_line import delete_po_line as _delete_po_line_row
from app.crud.po_line import get_po_line
from app.models.deletion_request import DeletionRequest, DeletionRequestStatus
from app.models.po_line import POLine
from app.models.user import User


class DeletionRequestError(Exception):
    """Base for deletion-request-specific errors — routes turn these into HTTP errors."""


class DuplicatePendingRequestError(DeletionRequestError):
    """Raised when a PO line already has an unresolved pending request."""


class InvalidStatusTransitionError(DeletionRequestError):
    """Raised when trying to approve/reject a request that's already been resolved."""


def list_deletion_requests(db: Session, status_filter: str | None = None) -> list[DeletionRequest]:
    stmt = select(DeletionRequest).order_by(DeletionRequest.created_at.desc())
    if status_filter:
        stmt = stmt.where(DeletionRequest.status == status_filter)
    return list(db.scalars(stmt))


def get_deletion_request(db: Session, request_id: int) -> DeletionRequest | None:
    return db.get(DeletionRequest, request_id)


def create_deletion_request(
    db: Session, po_line: POLine, reason: str, current_user: User
) -> DeletionRequest:
    existing = db.scalar(
        select(DeletionRequest).where(
            DeletionRequest.po_line_id == po_line.id,
            DeletionRequest.status == DeletionRequestStatus.PENDING,
        )
    )
    if existing:
        raise DuplicatePendingRequestError(
            f"A deletion request for PO {po_line.po_number} line {po_line.po_line} is already pending"
        )

    request = DeletionRequest(
        po_line_id=po_line.id,
        po_number=po_line.po_number,
        po_line=po_line.po_line,
        requested_by_id=current_user.id,
        reason=reason,
        status=DeletionRequestStatus.PENDING,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def approve_deletion_request(
    db: Session, request: DeletionRequest, current_user: User, resolution_notes: str | None
) -> DeletionRequest:
    if request.status != DeletionRequestStatus.PENDING:
        raise InvalidStatusTransitionError("Only a pending request can be approved")

    po_line = get_po_line(db, request.po_line_id) if request.po_line_id else None
    if po_line is not None:
        _delete_po_line_row(db, po_line)  # this commits the delete
        # Postgres already applied ON DELETE SET NULL to the po_line_id column
        # in the database, but SQLAlchemy's in-memory copy of `request` doesn't
        # know that happened automatically — set it explicitly so the object
        # we return (and the response built from it) reflects reality rather
        # than a now-stale foreign key value.
        request.po_line_id = None

    request.status = DeletionRequestStatus.APPROVED
    request.reviewed_by_id = current_user.id
    request.reviewed_at = datetime.now(UTC)
    request.resolution_notes = resolution_notes
    db.commit()
    db.refresh(request)
    return request


def reject_deletion_request(
    db: Session, request: DeletionRequest, current_user: User, resolution_notes: str | None
) -> DeletionRequest:
    if request.status != DeletionRequestStatus.PENDING:
        raise InvalidStatusTransitionError("Only a pending request can be rejected")

    request.status = DeletionRequestStatus.REJECTED
    request.reviewed_by_id = current_user.id
    request.reviewed_at = datetime.now(UTC)
    request.resolution_notes = resolution_notes
    db.commit()
    db.refresh(request)
    return request
