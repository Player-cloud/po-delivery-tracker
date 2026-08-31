import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Computed,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    case,
    func,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Priority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Status(str, enum.Enum):
    UPCOMING = "Upcoming"
    DUE_TODAY = "Due Today"
    OVERDUE = "Overdue"
    DELIVERED = "Delivered"


class POLine(Base):
    """
    One row per PO line — mirrors the SharePoint list schema from the original
    design document, with (po_number, po_line) enforced as a unique key (FR-1, FR-2).

    days_remaining and status are intentionally NOT stored columns (FR-5): they're
    computed from `promised_delivery` relative to the current date, either in Python
    (hybrid_property getter, for a loaded instance) or in SQL (hybrid_property
    .expression, for filtering/sorting directly in a query) so they're always correct
    without a daily refresh job.
    """

    __tablename__ = "po_lines"
    __table_args__ = (
        UniqueConstraint("po_number", "po_line", name="uq_po_number_po_line"),
        # Speeds up the dashboard's main query: open lines ordered by due date
        Index("ix_po_lines_open_by_due_date", "delivered", "promised_delivery"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    po_number: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    po_line: Mapped[int] = mapped_column(Integer, nullable=False)

    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    promised_delivery: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    delivered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # Required (PRD §14 Q2): every PO line has an owner who receives its reminders.
    assigned_to_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    priority: Mapped[Priority | None] = mapped_column(
        Enum(Priority, name="priority", native_enum=False), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Stored, DB-generated column: safe to persist because it only depends on
    # other stored columns (unlike days_remaining, which depends on "today").
    lead_time_days: Mapped[int | None] = mapped_column(
        Integer,
        Computed("promised_delivery - issue_date", persisted=True),
        nullable=True,
    )

    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    modified_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    assigned_to = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_po_lines")
    created_by = relationship("User", foreign_keys=[created_by_id])
    modified_by = relationship("User", foreign_keys=[modified_by_id])

    attachments = relationship("Attachment", back_populates="po_line", cascade="all, delete-orphan")
    notifications = relationship("NotificationHistory", back_populates="po_line", cascade="all, delete-orphan")

    # ---- computed, never stored ----

    @hybrid_property
    def days_remaining(self) -> int:
        """Python-side value, used when a POLine instance is already loaded."""
        return (self.promised_delivery - date.today()).days

    @days_remaining.expression
    def days_remaining(cls):  # noqa: N805
        """SQL-side expression, used when filtering/sorting/ordering in a query,
        e.g. `session.query(POLine).filter(POLine.days_remaining <= 7)`.
        Postgres date subtraction already returns an integer number of days,
        same as the lead_time_days generated column above — no cast needed."""
        return cls.promised_delivery - func.current_date()

    @hybrid_property
    def status(self) -> Status:
        if self.delivered:
            return Status.DELIVERED
        remaining = self.days_remaining
        if remaining < 0:
            return Status.OVERDUE
        if remaining == 0:
            return Status.DUE_TODAY
        return Status.UPCOMING

    @status.expression
    def status(cls):  # noqa: N805
        remaining = cls.days_remaining
        return case(
            (cls.delivered.is_(True), Status.DELIVERED.value),
            (remaining < 0, Status.OVERDUE.value),
            (remaining == 0, Status.DUE_TODAY.value),
            else_=Status.UPCOMING.value,
        )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<POLine {self.po_number}-{self.po_line} status={self.status}>"