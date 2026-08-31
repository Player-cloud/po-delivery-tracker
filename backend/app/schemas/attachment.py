from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    po_line_id: int
    file_name: str
    content_type: str | None
    size_bytes: int | None
    uploaded_by_id: int | None
    uploaded_at: datetime
