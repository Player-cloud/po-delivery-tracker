from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Attachment(Base):
    """A file attached to a PO line (invoice, receipt, delivery photo — FR-7).

    `blob_path` is a backend-agnostic reference: a local filesystem path in dev,
    an Azure Blob Storage URL/key in production. The database never stores the
    file itself, only where to find it (see System Design §7).
    """

    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    po_line_id: Mapped[int] = mapped_column(ForeignKey("po_lines.id", ondelete="CASCADE"), nullable=False, index=True)

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    blob_path: Mapped[str] = mapped_column(String(500), nullable=False)

    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    po_line = relationship("POLine", back_populates="attachments")
    uploaded_by = relationship("User")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Attachment id={self.id} file_name={self.file_name!r}>"
