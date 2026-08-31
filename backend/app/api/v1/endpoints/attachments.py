"""PO line attachments (M3, FR-4). Files stream to `Storage` (local disk in dev,
Cloudflare R2 in prod); the DB keeps the metadata."""

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.crud import attachment as attachment_crud
from app.crud import po_line as po_line_crud
from app.crud.attachment import AttachmentValidationError
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.attachment import AttachmentOut
from app.services.storage import StorageError

router = APIRouter(prefix="/po-lines/{po_line_id}/attachments", tags=["attachments"])

_WRITERS = (UserRole.STAFF, UserRole.MANAGER, UserRole.ADMINISTRATOR)


def _get_line_or_404(db: Session, po_line_id: int):
    po_line = po_line_crud.get_po_line(db, po_line_id)
    if po_line is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PO line not found")
    return po_line


def _assert_can_see(po_line, user: User) -> None:
    if user.role == UserRole.STAFF and po_line.assigned_to_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this PO line"
        )


@router.get("", response_model=list[AttachmentOut])
def list_line_attachments(
    po_line_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    po_line = _get_line_or_404(db, po_line_id)
    _assert_can_see(po_line, current_user)
    return attachment_crud.list_attachments(db, po_line_id)


@router.post("", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
def upload_attachment(
    po_line_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITERS)),
):
    po_line = _get_line_or_404(db, po_line_id)
    _assert_can_see(po_line, current_user)

    data = file.file.read()
    try:
        return attachment_crud.create_attachment(
            db,
            po_line,
            file_name=file.filename or "file",
            content_type=file.content_type,
            data=data,
            uploader=current_user,
        )
    except AttachmentValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except StorageError as exc:  # pragma: no cover - infra failure
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"storage error: {exc}"
        ) from exc


@router.get("/{attachment_id}")
def download_attachment(
    po_line_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    po_line = _get_line_or_404(db, po_line_id)
    _assert_can_see(po_line, current_user)

    row = attachment_crud.get_attachment(db, attachment_id)
    if row is None or row.po_line_id != po_line_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    try:
        data = attachment_crud.load_bytes(row)
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Blob missing from storage"
        ) from exc

    return Response(
        content=data,
        media_type=row.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{row.file_name}"'},
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_line_attachment(
    po_line_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITERS)),
):
    po_line = _get_line_or_404(db, po_line_id)
    _assert_can_see(po_line, current_user)

    row = attachment_crud.get_attachment(db, attachment_id)
    if row is None or row.po_line_id != po_line_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    attachment_crud.delete_attachment(db, row)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
