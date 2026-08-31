"""Data-access for the reminder de-duplication log (PRD §10 steps 4-5).

`threshold_label` is the de-dupe key per line:
  - "30_day", "60_day", "90_day", ...  one-shot, sent once as the due date nears
  - "due_today"                          one-shot, on the due date
  - "overdue_2026-08-31"                 one *per calendar day* while overdue
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification_history import NotificationHistory


def already_sent(db: Session, po_line_id: int, threshold_label: str) -> bool:
    stmt = select(NotificationHistory.id).where(
        NotificationHistory.po_line_id == po_line_id,
        NotificationHistory.threshold_label == threshold_label,
    )
    return db.scalar(stmt) is not None


def record_sent(
    db: Session, po_line_id: int, threshold_label: str, recipient: str
) -> NotificationHistory:
    row = NotificationHistory(
        po_line_id=po_line_id,
        threshold_label=threshold_label,
        recipient=recipient,
    )
    db.add(row)
    db.flush()  # caller owns the commit
    return row
