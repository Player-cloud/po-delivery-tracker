"""
Data-access for PO line attachments (M3, FR-4).

The DB row records *where* a file is (`blob_path` = the storage key) and its
metadata; the bytes live in `Storage` (local disk in dev, R2 in prod). Uploads
are validated here — extension allowlist + size cap, both configurable
(`settings.attachment_*`, PRD §14 Q6).
"""
from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.attachment import Attachment
from app.models.po_line import POLine
from app.models.user import User
from app.services.storage import get_storage

settings = get_settings()

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


class AttachmentValidationError(Exception):
    """Bad upload (extension not allowed, or too large) — route turns this into a 400."""


def _safe_name(name: str) -> str:
    """Strip any path and reduce to a predictable slug — never trust the client name."""
    base = name.replace("\\", "/").split("/")[-1].strip() or "file"
    base = _UNSAFE.sub("_", base)
    return base[:120]


def _extension(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def validate_upload(file_name: str, size_bytes: int) -> None:
    ext = _extension(file_name)
    allowed = settings.attachment_allowed_extensions
    if ext not in allowed:
        raise AttachmentValidationError(
            f"file type .{ext or '?'} is not allowed — permitted: {', '.join(sorted(allowed))}"
        )
    if size_bytes > settings.attachment_max_bytes:
        mb = settings.attachment_max_bytes / (1024 * 1024)
        raise AttachmentValidationError(f"file is larger than the {mb:.0f} MB limit")
    if size_bytes == 0:
        raise AttachmentValidationError("file is empty")


def list_attachments(db: Session, po_line_id: int) -> list[Attachment]:
    return list(
        db.scalars(
            select(Attachment)
            .where(Attachment.po_line_id == po_line_id)
            .order_by(Attachment.uploaded_at.desc())
        )
    )


def get_attachment(db: Session, attachment_id: int) -> Attachment | None:
    return db.get(Attachment, attachment_id)


def create_attachment(
    db: Session,
    po_line: POLine,
    *,
    file_name: str,
    content_type: str | None,
    data: bytes,
    uploader: User,
) -> Attachment:
    validate_upload(file_name, len(data))

    safe = _safe_name(file_name)
    key = f"po_lines/{po_line.id}/{uuid.uuid4().hex}_{safe}"
    get_storage().save(key, data, content_type)

    row = Attachment(
        po_line_id=po_line.id,
        file_name=safe,
        content_type=content_type,
        size_bytes=len(data),
        blob_path=key,
        uploaded_by_id=uploader.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_attachment(db: Session, attachment: Attachment) -> None:
    get_storage().delete(attachment.blob_path)
    db.delete(attachment)
    db.commit()


def load_bytes(attachment: Attachment) -> bytes:
    return get_storage().load(attachment.blob_path)
