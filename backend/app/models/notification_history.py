from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class NotificationHistory(Base):
    """
    Logs every reminder email actually sent for a PO line.

    This is what lets the daily scheduler ask "has the 7-day reminder already
    gone out for this line?" with a simple query instead of re-deriving it, and
    gives Administrators a real audit trail of what was sent, to whom, and when
    (System Design §4 — new vs. the original SharePoint design).
    """

    __tablename__ = "notification_history"
    __table_args__ = (
        # Speeds up "has this threshold already been sent for this line?" checks
        Index("ix_notification_history_line_threshold", "po_line_id", "threshold_label"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    po_line_id: Mapped[int] = mapped_column(
        ForeignKey("po_lines.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # e.g. "30_day", "14_day", "7_day", "3_day", "1_day", "due_today", "overdue"
    threshold_label: Mapped[str] = mapped_column(String(50), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    po_line = relationship("POLine", back_populates="notifications")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<NotificationHistory po_line_id={self.po_line_id} threshold={self.threshold_label!r}>"
        )
