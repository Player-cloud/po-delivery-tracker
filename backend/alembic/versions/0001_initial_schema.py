"""initial schema: users, po_lines, attachments, notification_history, configuration

Revision ID: 0001
Revises:
Create Date: 2026-07-20

Note: hand-authored, then corrected once against a real autogenerate diff
(see backend/README.md §4) — fixed: NOT NULL on all server_default=now()
timestamp columns, and single unique indexes (not unique-constraint +
separate index) on users.email and configuration.key.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("administrator", "manager", "staff", "viewer", name="user_role", native_enum=False),
            nullable=False,
            server_default="staff",
        ),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    # unique=True here does the same job a separate unique constraint would —
    # one unique index, matching mapped_column(unique=True, index=True) on the model.
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # --- po_lines ---
    op.create_table(
        "po_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("po_number", sa.String(length=50), nullable=False),
        sa.Column("po_line", sa.Integer(), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("promised_delivery", sa.Date(), nullable=False),
        sa.Column("delivered", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("assigned_to_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "priority",
            sa.Enum("high", "medium", "low", name="priority", native_enum=False),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "lead_time_days",
            sa.Integer(),
            sa.Computed("promised_delivery - issue_date", persisted=True),
            nullable=True,
        ),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("modified_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint("po_number", "po_line", name="uq_po_number_po_line"),
    )
    op.create_index("ix_po_lines_po_number", "po_lines", ["po_number"])
    op.create_index("ix_po_lines_promised_delivery", "po_lines", ["promised_delivery"])
    op.create_index("ix_po_lines_delivered", "po_lines", ["delivered"])
    # Composite index for the dashboard's main query: open lines ordered by due date
    op.create_index(
        "ix_po_lines_open_by_due_date", "po_lines", ["delivered", "promised_delivery"]
    )

    # --- attachments ---
    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "po_line_id",
            sa.Integer(),
            sa.ForeignKey("po_lines.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("blob_path", sa.String(length=500), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_attachments_po_line_id", "attachments", ["po_line_id"])

    # --- notification_history ---
    op.create_table(
        "notification_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "po_line_id",
            sa.Integer(),
            sa.ForeignKey("po_lines.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("threshold_label", sa.String(length=50), nullable=False),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_notification_history_po_line_id", "notification_history", ["po_line_id"])
    # Speeds up "has this threshold already been sent for this line?" checks
    op.create_index(
        "ix_notification_history_line_threshold",
        "notification_history",
        ["po_line_id", "threshold_label"],
    )

    # --- configuration ---
    op.create_table(
        "configuration",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.String(length=500), nullable=False),
    )
    op.create_index("ix_configuration_key", "configuration", ["key"], unique=True)

    # Seed the default reminder thresholds so the app has sane values on first run
    op.execute(
        "INSERT INTO configuration (key, value) "
        "VALUES ('reminder_thresholds_days', '30,14,7,3,1,0')"
    )


def downgrade() -> None:
    op.drop_table("configuration")
    op.drop_index("ix_notification_history_line_threshold", table_name="notification_history")
    op.drop_index("ix_notification_history_po_line_id", table_name="notification_history")
    op.drop_table("notification_history")
    op.drop_index("ix_attachments_po_line_id", table_name="attachments")
    op.drop_table("attachments")
    op.drop_index("ix_po_lines_open_by_due_date", table_name="po_lines")
    op.drop_index("ix_po_lines_delivered", table_name="po_lines")
    op.drop_index("ix_po_lines_promised_delivery", table_name="po_lines")
    op.drop_index("ix_po_lines_po_number", table_name="po_lines")
    op.drop_table("po_lines")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")