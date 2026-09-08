"""Reports (M8, PRD §18.5). Anyone signed in can run these — Viewer included.

Each report starts from the caller's *visible* PO lines (crud.po_line.list_po_lines
applies the same staff-only-sees-own rule as the rest of the app), filters in
Python at NFR-1 volumes, and returns a plain table: `columns` + `rows`, plus an
optional `summary` dict for the aggregate reports.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from app.crud.po_line import list_po_lines
from app.models.po_line import DeliveryStatus, POLine
from app.models.user import User


@dataclass
class ReportFilters:
    from_date: date | None = None
    to_date: date | None = None
    assignee_id: int | None = None
    po: str | None = None
    priority: str | None = None
    delivery_status: str | None = None


@dataclass
class Report:
    name: str
    label: str
    columns: list[dict[str, str]]  # [{key, label}]
    rows: list[dict]
    summary: dict | None = None
    generated_for: str = ""
    filters: dict = field(default_factory=dict)


def _assignee_name(line: POLine) -> str:
    u = line.assigned_to
    if u is None:
        return "—"
    return u.full_name or u.email


def _common_filter(lines: list[POLine], f: ReportFilters) -> list[POLine]:
    out = lines
    if f.assignee_id is not None:
        out = [l for l in out if l.assigned_to_id == f.assignee_id]
    if f.po:
        needle = f.po.lower()
        out = [l for l in out if needle in (l.po_number or "").lower()]
    if f.priority:
        out = [l for l in out if l.priority is not None and l.priority.value == f.priority]
    if f.delivery_status:
        out = [l for l in out if l.delivery_status.value == f.delivery_status]
    return out


# --- individual reports -------------------------------------------------------


def _overdue(lines: list[POLine], f: ReportFilters) -> Report:
    rows = []
    for l in _common_filter(lines, f):
        if l.delivery_status == DeliveryStatus.COMPLETE or l.days_remaining >= 0:
            continue
        if f.from_date and l.promised_delivery < f.from_date:
            continue
        if f.to_date and l.promised_delivery > f.to_date:
            continue
        rows.append(
            {
                "po_number": l.po_number,
                "po_line": l.po_line,
                "promised_delivery": l.promised_delivery.isoformat(),
                "days_overdue": -l.days_remaining,
                "delivery_status": l.delivery_status.value,
                "assignee": _assignee_name(l),
                "priority": l.priority.value if l.priority else "",
            }
        )
    rows.sort(key=lambda r: r["days_overdue"], reverse=True)
    return Report(
        name="overdue",
        label="Overdue lines",
        columns=[
            {"key": "po_number", "label": "PO"},
            {"key": "po_line", "label": "Line"},
            {"key": "promised_delivery", "label": "Promised"},
            {"key": "days_overdue", "label": "Days overdue"},
            {"key": "delivery_status", "label": "Delivery"},
            {"key": "assignee", "label": "Assignee"},
            {"key": "priority", "label": "Priority"},
        ],
        rows=rows,
        summary={"count": len(rows)},
    )


def _deliveries(lines: list[POLine], f: ReportFilters) -> Report:
    rows = []
    for l in _common_filter(lines, f):
        if l.delivery_status != DeliveryStatus.COMPLETE or l.delivered_at is None:
            continue
        d = l.delivered_at.date()
        if f.from_date and d < f.from_date:
            continue
        if f.to_date and d > f.to_date:
            continue
        rows.append(
            {
                "po_number": l.po_number,
                "po_line": l.po_line,
                "promised_delivery": l.promised_delivery.isoformat(),
                "delivered_on": d.isoformat(),
                "on_time": "Yes" if l.delivered_on_time else "No",
                "assignee": _assignee_name(l),
            }
        )
    rows.sort(key=lambda r: r["delivered_on"], reverse=True)
    on_time = sum(1 for r in rows if r["on_time"] == "Yes")
    return Report(
        name="deliveries",
        label="Deliveries",
        columns=[
            {"key": "po_number", "label": "PO"},
            {"key": "po_line", "label": "Line"},
            {"key": "promised_delivery", "label": "Promised"},
            {"key": "delivered_on", "label": "Delivered on"},
            {"key": "on_time", "label": "On time"},
            {"key": "assignee", "label": "Assignee"},
        ],
        rows=rows,
        summary={
            "count": len(rows),
            "on_time": on_time,
            "late": len(rows) - on_time,
            "on_time_pct": round(100 * on_time / len(rows), 1) if rows else None,
        },
    )


def _on_time(lines: list[POLine], f: ReportFilters) -> Report:
    completed = []
    for l in _common_filter(lines, f):
        if l.delivery_status != DeliveryStatus.COMPLETE or l.delivered_at is None:
            continue
        d = l.delivered_at.date()
        if f.from_date and d < f.from_date:
            continue
        if f.to_date and d > f.to_date:
            continue
        completed.append(l)

    by_assignee: dict[str, list[bool]] = {}
    for l in completed:
        by_assignee.setdefault(_assignee_name(l), []).append(bool(l.delivered_on_time))

    rows = []
    for name, flags in sorted(by_assignee.items()):
        ok = sum(flags)
        rows.append(
            {
                "assignee": name,
                "delivered": len(flags),
                "on_time": ok,
                "late": len(flags) - ok,
                "on_time_pct": round(100 * ok / len(flags), 1),
            }
        )

    total = len(completed)
    total_ok = sum(1 for l in completed if l.delivered_on_time)
    return Report(
        name="on_time",
        label="On-time delivery",
        columns=[
            {"key": "assignee", "label": "Assignee"},
            {"key": "delivered", "label": "Delivered"},
            {"key": "on_time", "label": "On time"},
            {"key": "late", "label": "Late"},
            {"key": "on_time_pct", "label": "On-time %"},
        ],
        rows=rows,
        summary={
            "delivered": total,
            "on_time": total_ok,
            "late": total - total_ok,
            "on_time_pct": round(100 * total_ok / total, 1) if total else None,
        },
    )


def _by_assignee(lines: list[POLine], f: ReportFilters) -> Report:
    buckets: dict[str, Counter] = {}
    for l in _common_filter(lines, f):
        c = buckets.setdefault(_assignee_name(l), Counter())
        c[l.delivery_status.value] += 1
        if l.delivery_status != DeliveryStatus.COMPLETE and l.days_remaining < 0:
            c["overdue"] += 1
        c["total"] += 1
    rows = [
        {
            "assignee": name,
            "not_delivered": c["not_delivered"],
            "partial": c["partial"],
            "complete": c["complete"],
            "overdue": c["overdue"],
            "total": c["total"],
        }
        for name, c in sorted(buckets.items())
    ]
    return Report(
        name="by_assignee",
        label="Lines by assignee",
        columns=[
            {"key": "assignee", "label": "Assignee"},
            {"key": "not_delivered", "label": "Not delivered"},
            {"key": "partial", "label": "Partial"},
            {"key": "complete", "label": "Complete"},
            {"key": "overdue", "label": "Overdue"},
            {"key": "total", "label": "Total"},
        ],
        rows=rows,
    )


def _by_status(lines: list[POLine], f: ReportFilters) -> Report:
    counts: Counter = Counter({s.value: 0 for s in DeliveryStatus})
    for l in _common_filter(lines, f):
        counts[l.delivery_status.value] += 1
    total = sum(counts.values())
    rows = [
        {
            "delivery_status": k.replace("_", " ").title(),
            "lines": n,
            "share": f"{round(100 * n / total)}%" if total else "0%",
        }
        for k, n in counts.items()
    ]
    return Report(
        name="by_status",
        label="Lines by delivery status",
        columns=[
            {"key": "delivery_status", "label": "Delivery status"},
            {"key": "lines", "label": "Lines"},
            {"key": "share", "label": "Share"},
        ],
        rows=rows,
    )


_BUILDERS = {
    "overdue": _overdue,
    "deliveries": _deliveries,
    "on_time": _on_time,
    "by_assignee": _by_assignee,
    "by_status": _by_status,
}

REPORTS_META = [
    {
        "name": "overdue",
        "label": "Overdue lines",
        "description": "Every open line past its promised date.",
    },
    {
        "name": "deliveries",
        "label": "Deliveries",
        "description": "Lines completed within a date range.",
    },
    {
        "name": "on_time",
        "label": "On-time delivery",
        "description": "On-time vs late completions, by assignee.",
    },
    {
        "name": "by_assignee",
        "label": "Lines by assignee",
        "description": "Line counts per person, by delivery status.",
    },
    {
        "name": "by_status",
        "label": "Lines by delivery status",
        "description": "How lines and quantity split across delivery states.",
    },
]


def available() -> list[dict]:
    return REPORTS_META


def build(db: Session, current_user: User, name: str, filters: ReportFilters) -> Report | None:
    builder = _BUILDERS.get(name)
    if builder is None:
        return None
    lines = list_po_lines(db, current_user)
    report = builder(lines, filters)
    report.generated_for = current_user.full_name or current_user.email
    report.filters = {
        k: (v.isoformat() if isinstance(v, date) else v)
        for k, v in vars(filters).items()
        if v is not None
    }
    return report
