from pydantic import BaseModel


class DashboardSummary(BaseModel):
    """Backs the KPI cards and the urgency composition bar on the dashboard.

    `overdue`, `due_today`, `due_soon`, `later` are a non-overlapping partition of
    the open (undelivered) lines — they sum to `total_open` — so the dashboard can
    draw a clean urgency composition bar. `due_this_week` (FR-15) still includes
    today and overlaps the others, so it stays a KPI card only.

    M8 adds PO-level counts and `due_1_30` (which replaces the `due_today` card on
    the redesigned dashboard). The pre-M8 fields are kept so the deployed frontend
    keeps working until Phase 3 switches over.
    """

    # pre-M8 (kept for back-compat)
    total_open: int
    due_today: int
    due_this_week: int
    due_soon: int  # 1..7 days out (this-week, excluding today and overdue)
    later: int  # more than 7 days out
    overdue: int
    completed: int
    high_priority: int

    # M8
    total_pos: int
    total_po_lines: int
    pos_delivered: int
    pos_closed: int
    due_1_30: int  # open lines 1..30 days out — replaces the "Due today" card
