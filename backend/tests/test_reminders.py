"""Unit tests for the M1 reminder engine (PRD §10).

Focus is `choose_reminder` — the pure decision logic that decides which single
reminder label applies to a line on a given day. The DB orchestration in
`run_reminders` is thin glue over this plus `notification_history` de-dup.
"""
from datetime import date
from types import SimpleNamespace

import pytest

from app.services.reminders import (
    ReminderDecision,
    _build_message,
    _recipient_for,
    choose_reminder,
)

TODAY = date(2026, 8, 31)
# Descending, like get_thresholds() returns after set_thresholds() sorts it.
THRESHOLDS = [90, 60, 30]
FINE_THRESHOLDS = [30, 14, 7, 3, 1, 0]


class TestChooseReminderPreDue:
    def test_nothing_due_when_further_out_than_largest_threshold(self):
        assert choose_reminder(120, THRESHOLDS, TODAY) is None

    def test_fires_nearest_passed_threshold_not_all_of_them(self):
        # 45 days out: both 90 and 60 windows are "passed", but only the
        # nearest (60) should fire — no burst of three emails.
        decision = choose_reminder(45, THRESHOLDS, TODAY)
        assert decision is not None
        assert decision.label == "60_day"
        assert decision.phrase == "is due in 45 days"

    def test_crossing_into_a_tighter_window_switches_label(self):
        assert choose_reminder(25, THRESHOLDS, TODAY).label == "30_day"

    def test_exact_threshold_boundary_counts_as_passed(self):
        assert choose_reminder(90, THRESHOLDS, TODAY).label == "90_day"

    def test_one_day_out_is_singular(self):
        decision = choose_reminder(1, FINE_THRESHOLDS, TODAY)
        assert decision.label == "1_day"
        assert decision.phrase == "is due in 1 day"

    def test_zero_in_threshold_list_is_ignored_due_today_handled_separately(self):
        # 0 in the list must not produce a "0_day" label.
        decision = choose_reminder(0, FINE_THRESHOLDS, TODAY)
        assert decision.label == "due_today"


class TestChooseReminderDueToday:
    def test_due_today(self):
        decision = choose_reminder(0, THRESHOLDS, TODAY)
        assert decision == ReminderDecision(label="due_today", phrase="is due today", days_remaining=0)

    def test_due_today_fires_even_if_no_threshold_window_configured(self):
        assert choose_reminder(0, [], TODAY).label == "due_today"


class TestChooseReminderOverdue:
    def test_overdue_label_is_date_stamped_for_daily_dedup(self):
        decision = choose_reminder(-1, THRESHOLDS, TODAY)
        assert decision.label == "overdue_2026-08-31"
        assert decision.phrase == "is overdue by 1 day"

    def test_overdue_label_changes_with_the_day(self):
        d1 = choose_reminder(-3, THRESHOLDS, date(2026, 8, 31))
        d2 = choose_reminder(-4, THRESHOLDS, date(2026, 9, 1))
        assert d1.label != d2.label  # so tomorrow's reminder is not de-duped against today's

    def test_overdue_plural(self):
        assert choose_reminder(-10, THRESHOLDS, TODAY).phrase == "is overdue by 10 days"

    def test_overdue_beats_a_pending_pre_due_label(self):
        # Went from +2 to -1 over a weekend: overdue wins, "1_day" is skipped.
        assert choose_reminder(-1, FINE_THRESHOLDS, TODAY).label.startswith("overdue_")


class TestOverdueEscalation:
    def test_not_escalated_within_the_window(self):
        d = choose_reminder(-7, THRESHOLDS, TODAY, overdue_escalation_days=7)
        assert d.escalate is False

    def test_escalated_past_the_window(self):
        d = choose_reminder(-8, THRESHOLDS, TODAY, overdue_escalation_days=7)
        assert d.escalate is True
        assert d.label == "overdue_2026-08-31"  # dedupe key unchanged by escalation

    def test_never_escalates_when_window_not_configured(self):
        assert choose_reminder(-40, THRESHOLDS, TODAY).escalate is False

    def test_pre_due_is_never_escalated(self):
        assert choose_reminder(5, THRESHOLDS, TODAY, overdue_escalation_days=7).escalate is False


class TestRecipientResolution:
    def _line(self, assignee=None):
        return SimpleNamespace(assigned_to=assignee)

    def _decision(self, escalate=False):
        return ReminderDecision(label="x", phrase="y", days_remaining=-1, escalate=escalate)

    def test_active_assignee_email_used(self):
        line = self._line(SimpleNamespace(active=True, email="a@corp.test"))
        assert _recipient_for(line, self._decision()) == "a@corp.test"

    def test_inactive_assignee_falls_back(self, monkeypatch):
        from app.services import reminders

        monkeypatch.setattr(reminders.settings, "reminder_fallback_email", "ops@corp.test")
        line = self._line(SimpleNamespace(active=False, email="a@corp.test"))
        assert _recipient_for(line, self._decision()) == "ops@corp.test"

    def test_no_assignee_no_fallback_returns_none(self, monkeypatch):
        from app.services import reminders

        monkeypatch.setattr(reminders.settings, "reminder_fallback_email", None)
        assert _recipient_for(self._line(), self._decision()) is None

    def test_escalated_decision_routes_to_escalation_email(self, monkeypatch):
        from app.services import reminders

        monkeypatch.setattr(reminders.settings, "reminder_escalation_email", "mgr@corp.test")
        line = self._line(SimpleNamespace(active=True, email="a@corp.test"))
        assert _recipient_for(line, self._decision(escalate=True)) == "mgr@corp.test"

    def test_escalated_falls_through_to_assignee_when_no_escalation_email(self, monkeypatch):
        from app.services import reminders

        monkeypatch.setattr(reminders.settings, "reminder_escalation_email", None)
        line = self._line(SimpleNamespace(active=True, email="a@corp.test"))
        assert _recipient_for(line, self._decision(escalate=True)) == "a@corp.test"


class TestMessageBody:
    def test_body_has_all_required_fields_and_link(self, monkeypatch):
        from app.services import reminders

        monkeypatch.setattr(reminders.settings, "frontend_base_url", "https://po.corp.test/")
        line = SimpleNamespace(
            id=42,
            po_number="ABC123",
            po_line=4,
            issue_date=date(2026, 8, 1),
            promised_delivery=date(2026, 9, 7),
            lead_time_days=37,
            status=SimpleNamespace(value="Upcoming"),
            assigned_to=SimpleNamespace(email="owner@corp.test"),
        )
        decision = choose_reminder(7, FINE_THRESHOLDS, TODAY)
        msg = _build_message(line, decision, "a@corp.test")

        assert msg.subject == "PO ABC123 - Line 4 is due in 7 days"
        for fragment in ("ABC123", "2026-08-01", "2026-09-07", "37", "Upcoming",
                         "owner@corp.test", "https://po.corp.test/po-lines/42/edit"):
            assert fragment in msg.text_body

    def test_escalated_message_is_marked_and_explained(self, monkeypatch):
        from app.services import reminders

        monkeypatch.setattr(reminders.settings, "frontend_base_url", "http://x")
        line = SimpleNamespace(
            id=1, po_number="P", po_line=1,
            issue_date=date(2026, 8, 1), promised_delivery=date(2026, 8, 20),
            lead_time_days=19, status=SimpleNamespace(value="Overdue"),
            assigned_to=SimpleNamespace(email="owner@corp.test"),
        )
        decision = choose_reminder(-11, THRESHOLDS, TODAY, overdue_escalation_days=7)
        msg = _build_message(line, decision, "mgr@corp.test")

        assert msg.subject.startswith("[ESCALATED] ")
        assert "escalated to you" in msg.text_body
        assert "//po-lines" not in msg.text_body  # trailing slash on base url handled


@pytest.mark.parametrize(
    "days_remaining, expected",
    [
        (365, None),
        (90, "90_day"),
        (61, "90_day"),
        (60, "60_day"),
        (31, "60_day"),
        (30, "30_day"),
        (1, "30_day"),
        (0, "due_today"),
        (-1, "overdue_2026-08-31"),
    ],
)
def test_threshold_walk(days_remaining, expected):
    decision = choose_reminder(days_remaining, THRESHOLDS, TODAY)
    assert (decision.label if decision else None) == expected
