from pydantic import BaseModel


class DashboardSummary(BaseModel):
    """Backs the KPI cards in the dashboard mockup (design doc §8.2)."""

    total_open: int
    due_today: int
    due_this_week: int
    overdue: int
    completed: int
    high_priority: int
