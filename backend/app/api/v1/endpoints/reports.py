from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services import reports
from app.services.report_formats import CONTENT_TYPES, render

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("")
def list_reports(_: User = Depends(get_current_user)) -> list[dict]:
    """The reports anyone signed in can run (PRD §18.5)."""
    return reports.available()


@router.get("/{name}")
def run_report(
    name: str,
    format: str = Query(default="json", pattern="^(json|csv|xlsx|pdf)$"),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    assignee_id: int | None = None,
    po: str | None = None,
    priority: str | None = Query(default=None, pattern="^(high|medium|low)$"),
    delivery_status: str | None = Query(default=None, pattern="^(not_delivered|partial|complete)$"),
    po_status: str | None = Query(default=None, pattern="^(open|delivered|closed|cancelled)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = reports.ReportFilters(
        from_date=from_date,
        to_date=to_date,
        assignee_id=assignee_id,
        po=po,
        priority=priority,
        delivery_status=delivery_status,
        po_status=po_status,
    )
    report = reports.build(db, current_user, name, filters)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown report {name!r}"
        )

    if format == "json":
        return {
            "name": report.name,
            "label": report.label,
            "columns": report.columns,
            "rows": report.rows,
            "summary": report.summary,
            "generated_for": report.generated_for,
            "filters": report.filters,
        }

    body = render(report, format)
    filename = f"{report.name}-{date.today().isoformat()}.{format}"
    return Response(
        content=body,
        media_type=CONTENT_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
