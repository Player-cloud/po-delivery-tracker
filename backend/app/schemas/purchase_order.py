from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.purchase_order import PurchaseOrderStatus
from app.schemas.po_line import POLineOut


class PurchaseOrderCreate(BaseModel):
    po_number: str

    @field_validator("po_number")
    @classmethod
    def _trim(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("PO number is required")
        return v


class PurchaseOrderAction(BaseModel):
    """Manual PO status change (PRD §18.3). close: Delivered→Closed; cancel:
    Open/Delivered→Cancelled; reopen: Closed/Cancelled→(recomputed from lines)."""

    action: Literal["close", "cancel", "reopen"]


class PurchaseOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    po_number: str
    status: PurchaseOrderStatus
    line_count: int
    lines_complete: int
    created_at: datetime
    modified_at: datetime


class PurchaseOrderDetail(PurchaseOrderOut):
    lines: list[POLineOut]
