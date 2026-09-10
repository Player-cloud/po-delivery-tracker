"""po_lines.description

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-10

Free-text description of what a line item is. Nullable — existing rows have none.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("po_lines", sa.Column("description", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("po_lines", "description")
