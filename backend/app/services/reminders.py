"""
M1 — the reminder engine (PRD §10).

`run_reminders()` is the single full pass invoked once a day by an external
scheduler via POST /api/v1/internal/run-reminders (GitHub Actions in prod, a
manual call or local cron in dev). Nothing here schedules itself, so it works on
a host that sleeps or scales to zero.

One pass:
  1. Load open (`delivered = False`) PO lines, oldest promised date first, capped
     at `reminder_batch_size`.
  2. For each line, `choose_reminder()` picks the single most urgent label that
     applies right now (overdue > due today > nearest passed threshold).
  3. If that label isn't already in `notification_history`, email the assigned
     user (or the fallback address) and log the send.
  4. Stop early once `reminder_max_emails_per_run` messages have gone out; the
     rest are picked up on the next daily run.

Delivered lines fall out of step 1 automatically — that's the stop condition
(FR-12), no explicit "cancel" needed.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.crud import notification_history as history_crud
from app.crud.configuration import get_thresholds
from app.models.po_line import POLine
from app.services.notifications import (
    EmailMessage,
    NotificationError,
    NotificationSender,
    get_notification_sender,
)

logger = logging.getLogger("app.reminders")
settings = get_settings()


@dataclass(frozen=True)
class ReminderDecision:
    """What to tell someone about one line, right now."""

    label: str          # de-dupe key for notification_history
    phrase: str         # human phrase for the subject line, e.g. "is due in 7 days"
    days_remaining: int
    escalate: bool = False  # overdue past the escalation window -> route to the escalation address


def choose_reminder(
    days_remaining: int,
    thresholds_days: list[int],
    today: date,
    overdue_escalation_days: int | None = None,
) -> ReminderDecision | None:
    """Pure decision logic — no DB, no dedup. Returns the one label that applies
    to a line with this `days_remaining`, or None if nothing is due yet.

    Priority: overdue (daily) > due today > nearest already-passed threshold.
    When `overdue_escalation_days` is given, a line more than that many days
    overdue is flagged `escalate=True` (PRD §14 Q3).
    """
    if days_remaining < 0:
        overdue_by = abs(days_remaining)
        unit = "day" if overdue_by == 1 else "days"
        escalate = overdue_escalation_days is not None and overdue_by > overdue_escalation_days
        # date-stamped so the once-per-day repeat de-dupes within a day but not across days
        return ReminderDecision(
            label=f"overdue_{today.isoformat()}",
            phrase=f"is overdue by {overdue_by} {unit}",
            days_remaining=days_remaining,
            escalate=escalate,
        )

    if days_remaining == 0:
        return ReminderDecision(
            label="due_today", phrase="is due today", days_remaining=0
        )

    # days_remaining > 0: has the line entered any configured pre-due window yet?
    passed = [t for t in thresholds_days if t > 0 and t >= days_remaining]
    if not passed:
        return None
    nearest = min(passed)
    unit = "day" if days_remaining == 1 else "days"
    return ReminderDecision(
        label=f"{nearest}_day",
        phrase=f"is due in {days_remaining} {unit}",
        days_remaining=days_remaining,
    )


@dataclass
class ReminderRunResult:
    thresholds_days: list[int]
    lines_scanned: int = 0
    emails_sent: int = 0
    emails_escalated: int = 0
    skipped_already_sent: int = 0
    skipped_no_recipient: int = 0
    errors: int = 0
    capped: bool = False
    details: list[str] = field(default_factory=list)


def _recipient_for(line: POLine, decision: ReminderDecision) -> str | None:
    """Resolution order (PRD §14 Q2/Q3):
    escalation address (only once past the overdue window) -> active assignee ->
    fallback address -> None (log and skip, retry next run).
    """
    if decision.escalate and settings.reminder_escalation_email:
        return settings.reminder_escalation_email
    user = line.assigned_to
    if user is not None and user.active and user.email:
        return user.email
    return settings.reminder_fallback_email


def _build_message(line: POLine, decision: ReminderDecision, recipient: str) -> EmailMessage:
    link = f"{settings.frontend_base_url.rstrip('/')}/po-lines/{line.id}/edit"
    subject = f"PO {line.po_number} - Line {line.po_line} {decision.phrase}"
    if decision.escalate:
        subject = f"[ESCALATED] {subject}"
    status = line.status.value if hasattr(line.status, "value") else str(line.status)
    assignee_email = line.assigned_to.email if line.assigned_to is not None else "-"
    text_body = (
        f"Purchase order {line.po_number}, line {line.po_line} {decision.phrase}.\n\n"
        f"  PO Number:          {line.po_number}\n"
        f"  PO Line:            {line.po_line}\n"
        f"  Issue Date:         {line.issue_date.isoformat()}\n"
        f"  Promised Delivery:  {line.promised_delivery.isoformat()}\n"
        f"  Lead Time (days):   {line.lead_time_days if line.lead_time_days is not None else '-'}\n"
        f"  Days Remaining:     {decision.days_remaining}\n"
        f"  Status:             {status}\n"
        f"  Assigned To:        {assignee_email}\n"
    )
    if decision.escalate:
        text_body += (
            "\nThis line is past the overdue-escalation window and has been "
            "escalated to you because the assignee has not marked it delivered.\n"
        )
    text_body += f"\nOpen this PO line: {link}\n"
    return EmailMessage(to=recipient, subject=subject, text_body=text_body)


def run_reminders(
    db: Session,
    *,
    today: date | None = None,
    sender: NotificationSender | None = None,
) -> ReminderRunResult:
    today = today or date.today()
    sender = sender or get_notification_sender()
    thresholds = sorted(get_thresholds(db), reverse=True)
    result = ReminderRunResult(thresholds_days=thresholds)

    stmt = (
        select(POLine)
        .where(POLine.delivered.is_(False))
        .options(joinedload(POLine.assigned_to))
        .order_by(POLine.promised_delivery.asc())
        .limit(settings.reminder_batch_size)
    )
    open_lines = db.scalars(stmt).all()

    for line in open_lines:
        result.lines_scanned += 1

        days_remaining = (line.promised_delivery - today).days
        decision = choose_reminder(
            days_remaining, thresholds, today, settings.reminder_overdue_escalation_days
        )
        if decision is None:
            continue

        if history_crud.already_sent(db, line.id, decision.label):
            result.skipped_already_sent += 1
            continue

        if result.emails_sent >= settings.reminder_max_emails_per_run:
            result.capped = True
            result.details.append(
                f"cap of {settings.reminder_max_emails_per_run} reached; "
                f"remaining lines deferred to the next run"
            )
            break

        recipient = _recipient_for(line, decision)
        if not recipient:
            result.skipped_no_recipient += 1
            result.details.append(
                f"PO {line.po_number}-{line.po_line}: no active assignee and no "
                f"REMINDER_FALLBACK_EMAIL / REMINDER_ESCALATION_EMAIL set — not sent, will retry next run"
            )
            continue

        try:
            sender.send(_build_message(line, decision, recipient))
        except NotificationError as exc:
            result.errors += 1
            result.details.append(f"PO {line.po_number}-{line.po_line}: send failed — {exc}")
            logger.warning("reminder send failed for po_line %s: %s", line.id, exc)
            db.rollback()
            continue

        history_crud.record_sent(db, line.id, decision.label, recipient)
        db.commit()  # per-send commit: a later crash never re-sends what already went out
        result.emails_sent += 1
        if decision.escalate:
            result.emails_escalated += 1
            result.details.append(
                f"PO {line.po_number}-{line.po_line}: escalated to {recipient} "
                f"({abs(days_remaining)} days overdue)"
            )

    logger.info(
        "reminder run complete: scanned=%d sent=%d escalated=%d already=%d no_recipient=%d errors=%d capped=%s",
        result.lines_scanned,
        result.emails_sent,
        result.emails_escalated,
        result.skipped_already_sent,
        result.skipped_no_recipient,
        result.errors,
        result.capped,
    )
    return result
