"""M8: purchase orders, quantity, delivery status, user full name

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-07

Promotes "PO" from a repeated varchar on po_lines to a real `purchase_orders`
row that owns its lines (PRD §18). Also:
  - po_lines gains `quantity` and a three-state `delivery_status` that replaces
    the `delivered` boolean;
  - users gain `full_name` (backfilled from the email local-part).

Enum columns store the member NAME (uppercase) — see the `local-db-alembic-drift`
note — so the data migration writes 'COMPLETE' / 'OPEN' etc., not lowercase.

Data migration assumes a modest number of existing rows (the production DB has a
handful). Each distinct po_lines.po_number becomes one purchase_orders row.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PO_STATUS = sa.Enum(
    "open", "delivered", "closed", "cancelled", name="purchase_order_status", native_enum=False
)
_DELIVERY_STATUS = sa.Enum(
    "not_delivered", "partial", "complete", name="delivery_status", native_enum=False
)


def upgrade() -> None:
    # --- purchase_orders ---
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("po_number", sa.String(length=50), nullable=False),
        sa.Column("status", _PO_STATUS, nullable=False, server_default="OPEN"),
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
    )
    op.create_index("ix_purchase_orders_po_number", "purchase_orders", ["po_number"], unique=True)
    op.create_index("ix_purchase_orders_status", "purchase_orders", ["status"])

    # --- po_lines: new columns, nullable for the backfill ---
    op.add_column(
        "po_lines",
        sa.Column("purchase_order_id", sa.Integer(), sa.ForeignKey("purchase_orders.id"), nullable=True),
    )
    op.add_column(
        "po_lines", sa.Column("quantity", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column(
        "po_lines",
        sa.Column("delivery_status", _DELIVERY_STATUS, nullable=False, server_default="NOT_DELIVERED"),
    )

    # --- users.full_name ---
    op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))

    # --- data migration ---
    # 1. one purchase_orders row per distinct po_number
    op.execute(
        """
        INSERT INTO purchase_orders (po_number, status, created_at, modified_at)
        SELECT DISTINCT po_number, 'OPEN', now(), now() FROM po_lines
        """
    )
    # 2. link every line to its PO
    op.execute(
        """
        UPDATE po_lines pl
        SET purchase_order_id = po.id
        FROM purchase_orders po
        WHERE po.po_number = pl.po_number
        """
    )
    # 3. delivered boolean -> delivery_status
    op.execute(
        "UPDATE po_lines SET delivery_status = 'COMPLETE' WHERE delivered = true"
    )
    # 4. a PO whose every line is COMPLETE is DELIVERED
    op.execute(
        """
        UPDATE purchase_orders po
        SET status = 'DELIVERED'
        WHERE NOT EXISTS (
            SELECT 1 FROM po_lines pl
            WHERE pl.purchase_order_id = po.id AND pl.delivery_status <> 'COMPLETE'
        )
        AND EXISTS (SELECT 1 FROM po_lines pl WHERE pl.purchase_order_id = po.id)
        """
    )
    # 5. backfill user names from the email local-part
    op.execute("UPDATE users SET full_name = split_part(email, '@', 1) WHERE full_name IS NULL")

    # --- lock down po_lines ---
    op.alter_column("po_lines", "purchase_order_id", existing_type=sa.Integer(), nullable=False)
    op.create_index("ix_po_lines_purchase_order_id", "po_lines", ["purchase_order_id"])
    op.create_index("ix_po_lines_delivery_status", "po_lines", ["delivery_status"])
    op.create_unique_constraint(
        "uq_po_line_per_po", "po_lines", ["purchase_order_id", "po_line"]
    )

    # --- drop the old po_number-based columns / indexes ---
    op.drop_index("ix_po_lines_open_by_due_date", table_name="po_lines")
    op.drop_index("ix_po_lines_delivered", table_name="po_lines")
    op.drop_index("ix_po_lines_po_number", table_name="po_lines")
    op.drop_constraint("uq_po_number_po_line", "po_lines", type_="unique")
    op.drop_column("po_lines", "delivered")
    op.drop_column("po_lines", "po_number")
    op.create_index(
        "ix_po_lines_open_by_due_date", "po_lines", ["delivery_status", "promised_delivery"]
    )

    # server_defaults were only needed to backfill NOT NULL columns on existing rows
    op.alter_column("po_lines", "quantity", server_default=None)
    op.alter_column("po_lines", "delivery_status", server_default=None)
    op.alter_column("purchase_orders", "status", server_default=None)


def downgrade() -> None:
    op.add_column("po_lines", sa.Column("po_number", sa.String(length=50), nullable=True))
    op.add_column(
        "po_lines", sa.Column("delivered", sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.execute(
        """
        UPDATE po_lines pl
        SET po_number = po.po_number
        FROM purchase_orders po
        WHERE po.id = pl.purchase_order_id
        """
    )
    op.execute("UPDATE po_lines SET delivered = true WHERE delivery_status = 'COMPLETE'")
    op.alter_column("po_lines", "po_number", existing_type=sa.String(length=50), nullable=False)

    op.drop_index("ix_po_lines_open_by_due_date", table_name="po_lines")
    op.drop_constraint("uq_po_line_per_po", "po_lines", type_="unique")
    op.drop_index("ix_po_lines_delivery_status", table_name="po_lines")
    op.drop_index("ix_po_lines_purchase_order_id", table_name="po_lines")
    op.drop_column("po_lines", "delivery_status")
    op.drop_column("po_lines", "quantity")
    op.drop_column("po_lines", "purchase_order_id")

    op.create_index("ix_po_lines_po_number", "po_lines", ["po_number"])
    op.create_index("ix_po_lines_delivered", "po_lines", ["delivered"])
    op.create_index(
        "ix_po_lines_open_by_due_date", "po_lines", ["delivered", "promised_delivery"]
    )
    op.create_unique_constraint("uq_po_number_po_line", "po_lines", ["po_number", "po_line"])

    op.drop_column("users", "full_name")

    op.drop_index("ix_purchase_orders_status", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_po_number", table_name="purchase_orders")
    op.drop_table("purchase_orders")
