"""make po_lines.assigned_to_id required (PRD §14 Q2)

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-31

Every PO line must have an owner who receives its reminders. Existing rows with
a NULL assignee are backfilled to the lowest-id user (typically the seeded
Administrator) before the NOT NULL constraint is applied — adjust those rows by
hand afterwards if a different owner is correct.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Backfill: if this UPDATE can't find a user, the SET NOT NULL below will
    # fail loudly — which is the right outcome for an otherwise-unseeded DB.
    op.execute(
        "UPDATE po_lines "
        "SET assigned_to_id = (SELECT id FROM users ORDER BY id LIMIT 1) "
        "WHERE assigned_to_id IS NULL"
    )
    op.alter_column("po_lines", "assigned_to_id", existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    op.alter_column("po_lines", "assigned_to_id", existing_type=sa.Integer(), nullable=True)
