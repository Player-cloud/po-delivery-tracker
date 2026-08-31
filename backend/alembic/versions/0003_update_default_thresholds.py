"""update default reminder thresholds from 30/14/7/3/1/0 to 30/60/90

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-27

This is a DATA migration, not a schema change — no table structure changes,
just the value of one seeded config row. Deliberately a new migration rather
than editing 0001: that migration already ran against real databases (yours
included), and editing it wouldn't retroactively change data that's already
there — only a new migration, applied going forward, actually does that.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The WHERE clause guards against overwriting a value someone already
    # changed themselves via PUT /config/thresholds — if it doesn't match the
    # original seed exactly, this simply updates nothing, which is correct.
    op.execute(
        "UPDATE configuration SET value = '30,60,90' "
        "WHERE key = 'reminder_thresholds_days' AND value = '30,14,7,3,1,0'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE configuration SET value = '30,14,7,3,1,0' "
        "WHERE key = 'reminder_thresholds_days' AND value = '30,60,90'"
    )
