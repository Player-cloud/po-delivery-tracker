"""M8 reports: po_lines.delivered_at

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-08

When a line last became COMPLETE — powers the "deliveries in a date range" and
on-time-% reports (PRD §18.5). Existing COMPLETE rows are backfilled from
`modified_at` as the best available estimate.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "po_lines", sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.execute(
        "UPDATE po_lines SET delivered_at = modified_at WHERE delivery_status = 'COMPLETE'"
    )
    op.create_index("ix_po_lines_delivered_at", "po_lines", ["delivered_at"])


def downgrade() -> None:
    op.drop_index("ix_po_lines_delivered_at", table_name="po_lines")
    op.drop_column("po_lines", "delivered_at")
