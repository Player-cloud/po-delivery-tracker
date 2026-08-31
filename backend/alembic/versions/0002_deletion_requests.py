"""deletion requests: staff-submitted delete requests with admin approval history

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "deletion_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        # SET NULL, not CASCADE — deliberately. See app/models/deletion_request.py
        # for why: CASCADE would destroy this audit row the instant it's used.
        sa.Column(
            "po_line_id",
            sa.Integer(),
            sa.ForeignKey("po_lines.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("po_number", sa.String(length=50), nullable=False),
        sa.Column("po_line", sa.Integer(), nullable=False),
        sa.Column("requested_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "approved", "rejected", name="deletion_request_status", native_enum=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("reviewed_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_deletion_requests_po_line_id", "deletion_requests", ["po_line_id"])


def downgrade() -> None:
    op.drop_index("ix_deletion_requests_po_line_id", table_name="deletion_requests")
    op.drop_table("deletion_requests")
