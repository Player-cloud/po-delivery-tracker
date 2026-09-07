import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.po_line import DeliveryStatus


class PurchaseOrderStatus(str, enum.Enum):
    """OPEN and DELIVERED are managed automatically from the lines
    (`recompute_status`); CLOSED and CANCELLED are manual manager/admin actions."""

    OPEN = "open"
    DELIVERED = "delivered"
    CLOSED = "closed"
    CANCELLED = "cancelled"


_AUTO_STATES = (PurchaseOrderStatus.OPEN, PurchaseOrderStatus.DELIVERED)


class PurchaseOrder(Base):
    """A purchase order — the batch that was ordered. Owns one or more `POLine`
    rows (M8, PRD §18). Its number is unique; its status is Open until every line
    is Complete (→ Delivered), then a manager can mark it Closed."""

    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    po_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(PurchaseOrderStatus, name="purchase_order_status", native_enum=False),
        nullable=False,
        default=PurchaseOrderStatus.OPEN,
        index=True,
    )

    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    modified_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lines = relationship(
        "POLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        order_by="POLine.po_line",
    )
    created_by = relationship("User", foreign_keys=[created_by_id])
    modified_by = relationship("User", foreign_keys=[modified_by_id])

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def lines_complete(self) -> int:
        return sum(1 for line in self.lines if line.delivery_status == DeliveryStatus.COMPLETE)

    def recompute_status(self) -> None:
        """Sync OPEN ⇄ DELIVERED from the lines. Never overrides a manual
        CLOSED / CANCELLED — call `reopen()` first if that's intended."""
        if self.status not in _AUTO_STATES:
            return
        all_complete = bool(self.lines) and all(
            line.delivery_status == DeliveryStatus.COMPLETE for line in self.lines
        )
        self.status = PurchaseOrderStatus.DELIVERED if all_complete else PurchaseOrderStatus.OPEN

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PurchaseOrder {self.po_number} status={self.status}>"
