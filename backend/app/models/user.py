import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class UserRole(str, enum.Enum):
    ADMINISTRATOR = "administrator"
    MANAGER = "manager"
    STAFF = "staff"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # Collected when an admin creates a user (M8). Nullable so the pre-M8 rows
    # stay valid; the create form requires it going forward.
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False), nullable=False, default=UserRole.STAFF
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # PO lines assigned to this user
    assigned_po_lines = relationship(
        "POLine", back_populates="assigned_to", foreign_keys="POLine.assigned_to_id"
    )

    @property
    def display_name(self) -> str:
        """Full name if we have one, else the email — for pickers and tables."""
        return self.full_name or self.email

    @property
    def first_name(self) -> str | None:
        """Best-effort first name for email greetings ("Hi Jane,")."""
        return self.full_name.split()[0] if self.full_name else None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email!r} role={self.role}>"
