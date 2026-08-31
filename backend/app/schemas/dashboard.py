from pydantic import BaseModel


class DashboardSummary(BaseModel):
    """Backs the KPI cards in the dashboard mockup (design doc §8.2).

    `overdue`, `due_today`, `due_soon`, `later` are a non-overlapping partition of
    the open (undelivered) lines — they sum to `total_open` — so the dashboard can
    draw a clean urgency composition bar. `due_this_week` (FR-15) still includes
    today and overlaps the others, so it stays a KPI card only.
    """

    total_open: int
    due_today: int
    due_this_week: int
    due_soon: int  # 1..7 days out (this-week, excluding today and overdue)
    later: int  # more than 7 days out
    overdue: int
    completed: int
    high_priority: int
