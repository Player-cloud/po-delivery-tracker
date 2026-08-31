from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.configuration import Configuration

THRESHOLDS_KEY = "reminder_thresholds_days"
# Single source of truth for the fallback — see Settings.default_reminder_thresholds_days.
DEFAULT_THRESHOLDS = get_settings().default_reminder_thresholds_days


def get_thresholds(db: Session) -> list[int]:
    row = db.scalar(select(Configuration).where(Configuration.key == THRESHOLDS_KEY))
    if row is None:
        return DEFAULT_THRESHOLDS
    return [int(x) for x in row.value.split(",") if x]


def set_thresholds(db: Session, thresholds: list[int]) -> list[int]:
    row = db.scalar(select(Configuration).where(Configuration.key == THRESHOLDS_KEY))
    value = ",".join(str(t) for t in thresholds)
    if row is None:
        db.add(Configuration(key=THRESHOLDS_KEY, value=value))
    else:
        row.value = value
    db.commit()
    return thresholds
