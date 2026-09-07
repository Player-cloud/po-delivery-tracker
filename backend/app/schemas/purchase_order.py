from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.purchase_order import PurchaseOrderStatus


class PurchaseOrderRef(BaseModel):
    """Minimal PO info embedded in a PO line response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    po_number: str
    status: PurchaseOrderStatus


class PurchaseOrderCreate(BaseModel):
    po_number: str


class PurchaseOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    po_number: str
    status: PurchaseOrderStatus
    line_count: int = 0
    created_at: datetime
    modified_at: datetime
