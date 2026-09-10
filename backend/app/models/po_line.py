import enum
from datetime import date, datetime

from sqlalchemy import (
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


class DeliveryStatus(str, enum.Enum):
    """Per-line delivery state (M8). Replaces the old `delivered` boolean:
    a line can be partially delivered while its remaining quantity is still
    tracked against the promised date."""

    NOT_DELIVERED = "not_delivered"
    PARTIAL = "partial"
    COMPLETE = "complete"


class Status(str, enum.Enum):
    UPCOMING = "Upcoming"
    DUE_TODAY = "Due Today"
    OVERDUE = "Overdue"
    DELIVERED = "Delivered"


class POLine(Base):
    """
    One item on a purchase order — the "1a / 1b / 1c" under a PO (M8). Belongs to
    exactly one `PurchaseOrder`; `po_line` is a plain integer unique within that PO.

    days_remaining and status are intentionally NOT stored columns (FR-5): they're
    computed from `promised_delivery` relative to the current date, either in Python
    (hybrid_property getter, for a loaded instance) or in SQL (hybrid_property
    .expression, for filtering/sorting directly in a query) so they're always correct
    without a daily refresh job.
    """

    __tablename__ = "po_lines"
    __table_args__ = (
        UniqueConstraint("purchase_order_id", "po_line", name="uq_po_line_per_po"),
        # Speeds up the dashboard's main query: open lines ordered by due date
        Index("ix_po_lines_open_by_due_date", "delivery_status", "promised_delivery"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id"), nullable=False, index=True
    )
    po_line: Mapped[int] = mapped_column(Integer, nullable=False)

    # Free-text "what this line item is".
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    promised_delivery: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    delivery_status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status", native_enum=False),
        nullable=False,
        default=DeliveryStatus.NOT_DELIVERED,
        index=True,
    )
    # When the line last became COMPLETE — cleared if it's reopened (M8 reports:
    # "deliveries in a date range", on-time %). Set by crud.po_line.
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

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

    purchase_order = relationship("PurchaseOrder", back_populates="lines")
    assigned_to = relationship(
        "User", foreign_keys=[assigned_to_id], back_populates="assigned_po_lines"
    )
    created_by = relationship("User", foreign_keys=[created_by_id])
    modified_by = relationship("User", foreign_keys=[modified_by_id])

    attachments = relationship("Attachment", back_populates="po_line", cascade="all, delete-orphan")
    notifications = relationship(
        "NotificationHistory", back_populates="po_line", cascade="all, delete-orphan"
    )

    # ---- convenience ----

    @property
    def po_number(self) -> str | None:
        """The parent PO's number. Read-only — set it on the PurchaseOrder."""
        return self.purchase_order.po_number if self.purchase_order is not None else None

    @property
    def delivered(self) -> bool:
        """Back-compat shim for callers that predate `delivery_status` (M8)."""
        return self.delivery_status == DeliveryStatus.COMPLETE

    @property
    def delivered_on_time(self) -> bool | None:
        """True/False once the line is COMPLETE and dated; None otherwise."""
        if self.delivery_status != DeliveryStatus.COMPLETE or self.delivered_at is None:
            return None
        return self.delivered_at.date() <= self.promised_delivery

    # ---- computed, never stored ----

    @hybrid_property
    def days_remaining(self) -> int:
        """Python-side value, used when a POLine instance is already loaded."""
        return (self.promised_delivery - date.today()).days

    @days_remaining.expression
    def days_remaining(cls):
        """SQL-side expression, used when filtering/sorting/ordering in a query,
        e.g. `session.query(POLine).filter(POLine.days_remaining <= 7)`.
        Postgres date subtraction already returns an integer number of days,
        same as the lead_time_days generated column above — no cast needed."""
        return cls.promised_delivery - func.current_date()

    @hybrid_property
    def status(self) -> Status:
        if self.delivery_status == DeliveryStatus.COMPLETE:
            return Status.DELIVERED
        remaining = self.days_remaining
        if remaining < 0:
            return Status.OVERDUE
        if remaining == 0:
            return Status.DUE_TODAY
        return Status.UPCOMING

    @status.expression
    def status(cls):
        remaining = cls.days_remaining
        return case(
            (cls.delivery_status == DeliveryStatus.COMPLETE, Status.DELIVERED.value),
            (remaining < 0, Status.OVERDUE.value),
            (remaining == 0, Status.DUE_TODAY.value),
            else_=Status.UPCOMING.value,
        )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<POLine {self.po_number}-{self.po_line} status={self.status}>"
