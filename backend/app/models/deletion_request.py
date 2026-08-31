import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class DeletionRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DeletionRequest(Base):
    """
    A Staff/Manager-submitted request to delete a PO line, and the permanent
    record of how an Administrator resolved it. This table IS the deletion
    audit trail — approving a request deletes the PO line; rejecting one
    leaves it untouched either way.

    po_line_id uses ondelete="SET NULL", deliberately NOT "CASCADE": if it
    cascaded, approving a request (which deletes the PO line) would then
    cascade-delete THIS row too, destroying the exact history this table
    exists to keep. SET NULL lets the PO line go while the request survives.
    po_number/po_line are a permanent snapshot, so the record stays readable
    even once po_line_id has gone null.
    """

    __tablename__ = "deletion_requests"

    id: Mapped[int] = mapped_column(primary_key=True)

    po_line_id: Mapped[int | None] = mapped_column(
        ForeignKey("po_lines.id", ondelete="SET NULL"), nullable=True, index=True
    )
    po_number: Mapped[str] = mapped_column(String(50), nullable=False)
    po_line: Mapped[int] = mapped_column(Integer, nullable=False)

    requested_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[DeletionRequestStatus] = mapped_column(
        Enum(DeletionRequestStatus, name="deletion_request_status", native_enum=False),
        nullable=False,
        default=DeletionRequestStatus.PENDING,
    )

    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    linked_po_line = relationship("POLine")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DeletionRequest {self.po_number}-{self.po_line} status={self.status}>"
