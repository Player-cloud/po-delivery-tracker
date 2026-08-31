from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class Configuration(Base):
    """
    Simple key/value store for business-editable settings — most importantly the
    reminder thresholds (FR-9: "configurable by an Administrator without a code
    change"). Example row: key="reminder_thresholds_days", value="30,14,7,3,1,0".

    Kept deliberately generic (key/value, not a dedicated thresholds table) so new
    configurable settings don't require a schema migration later.
    """

    __tablename__ = "configuration"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(String(500), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Configuration {self.key}={self.value!r}>"
