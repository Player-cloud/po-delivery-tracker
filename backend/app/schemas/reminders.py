from pydantic import BaseModel, ConfigDict


class ReminderRunOut(BaseModel):
    """Summary of one `POST /internal/run-reminders` pass."""

    model_config = ConfigDict(from_attributes=True)

    thresholds_days: list[int]
    lines_scanned: int
    emails_sent: int
    emails_escalated: int
    skipped_already_sent: int
    skipped_no_recipient: int
    errors: int
    capped: bool
    details: list[str]
