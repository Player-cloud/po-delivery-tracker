from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.crud.po_line import attention_lines, dashboard_summary
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummary
from app.schemas.po_line import POLineOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return dashboard_summary(db, current_user)


@router.get("/attention", response_model=list[POLineOut])
def get_attention_lines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Open PO lines needing attention now (overdue or due within a week),
    most urgent first — backs the dashboard 'Needs attention' list (FR-16)."""
    return attention_lines(db, current_user)
