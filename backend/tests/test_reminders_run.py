"""Integration tests for `run_reminders` — the full daily pass over the DB,
including notification_history de-dup, the per-run email cap, delivered-line
exclusion, and the no-recipient / send-failure paths.
"""

from datetime import date, timedelta

import pytest

from app.crud.configuration import set_thresholds
from app.crud.notification_history import already_sent
from app.services import reminders
from app.services.reminders import run_reminders

TODAY = date.today()


@pytest.fixture(autouse=True)
def _thresholds(db):
    set_thresholds(db, [30, 14, 7, 3, 1, 0])


def test_sends_one_reminder_per_line_and_logs_history(db, users, make_line, fake_sender):
    make_line(due_in_days=7, assigned_to=users["alice"])
    result = run_reminders(db, sender=fake_sender)

    assert result.emails_sent == 1
    assert fake_sender.sent[0].to == "alice@corp.test"
    assert "is due in 7 days" in fake_sender.sent[0].subject


def test_second_run_same_day_is_fully_deduped(db, users, make_line, fake_sender):
    make_line(due_in_days=7, assigned_to=users["alice"])
    run_reminders(db, sender=fake_sender)
    second = run_reminders(db, sender=fake_sender)

    assert second.emails_sent == 0
    assert second.skipped_already_sent == 1
    assert len(fake_sender.sent) == 1


def test_delivered_lines_are_never_reminded(db, users, make_line, fake_sender):
    make_line(due_in_days=2, delivered=True, assigned_to=users["alice"])
    result = run_reminders(db, sender=fake_sender)

    assert result.lines_scanned == 0
    assert result.emails_sent == 0


def test_overdue_sends_again_the_next_day(db, users, make_line, fake_sender):
    line = make_line(due_in_days=-2, assigned_to=users["alice"])

    run_reminders(db, sender=fake_sender, today=TODAY)
    run_reminders(db, sender=fake_sender, today=TODAY)  # same day: deduped
    assert len(fake_sender.sent) == 1

    run_reminders(db, sender=fake_sender, today=TODAY + timedelta(days=1))
    assert len(fake_sender.sent) == 2
    assert already_sent(db, line.id, f"overdue_{TODAY.isoformat()}")
    assert already_sent(db, line.id, f"overdue_{(TODAY + timedelta(days=1)).isoformat()}")


def test_no_recipient_is_skipped_not_recorded(db, users, make_line, fake_sender, monkeypatch):
    # Assigned To is required, but the assignee can be deactivated after the fact.
    monkeypatch.setattr(reminders.settings, "reminder_fallback_email", None)
    monkeypatch.setattr(reminders.settings, "reminder_escalation_email", None)
    line = make_line(due_in_days=1, assigned_to=users["bob"])  # inactive

    result = run_reminders(db, sender=fake_sender)

    assert result.skipped_no_recipient == 1
    assert result.emails_sent == 0
    # not recorded -> a later run (once the assignee is reactivated / reassigned) still delivers
    assert not already_sent(db, line.id, "1_day")


def test_inactive_assignee_uses_fallback_address(db, users, make_line, fake_sender, monkeypatch):
    monkeypatch.setattr(reminders.settings, "reminder_fallback_email", "ops@corp.test")
    make_line(due_in_days=1, assigned_to=users["bob"])  # bob is inactive

    run_reminders(db, sender=fake_sender)

    assert fake_sender.sent[0].to == "ops@corp.test"


def test_send_failure_is_isolated_and_retried_next_run(db, users, make_line):
    from tests.conftest import FakeSender

    make_line(due_in_days=1, assigned_to=users["alice"])
    failing = FakeSender(fail_for={"alice@corp.test"})

    first = run_reminders(db, sender=failing)
    assert first.errors == 1
    assert first.emails_sent == 0

    ok = FakeSender()
    second = run_reminders(db, sender=ok)
    assert second.emails_sent == 1  # not deduped — first attempt was never recorded


def test_per_run_cap_defers_the_rest(db, users, make_line, fake_sender, monkeypatch):
    monkeypatch.setattr(reminders.settings, "reminder_max_emails_per_run", 2)
    for _ in range(5):
        make_line(due_in_days=1, assigned_to=users["alice"])

    result = run_reminders(db, sender=fake_sender)

    assert result.emails_sent == 2
    assert result.capped is True

    monkeypatch.setattr(reminders.settings, "reminder_max_emails_per_run", 90)
    result2 = run_reminders(db, sender=fake_sender)
    assert result2.emails_sent == 3
    assert result2.capped is False


def test_batch_size_limits_lines_scanned(db, users, make_line, fake_sender, monkeypatch):
    monkeypatch.setattr(reminders.settings, "reminder_batch_size", 3)
    for _ in range(5):
        make_line(due_in_days=100, assigned_to=users["alice"])  # far out: no email, just scanned

    result = run_reminders(db, sender=fake_sender)
    assert result.lines_scanned == 3


class TestOverdueEscalation:
    @pytest.fixture(autouse=True)
    def _escalation_config(self, monkeypatch):
        monkeypatch.setattr(reminders.settings, "reminder_overdue_escalation_days", 7)
        monkeypatch.setattr(reminders.settings, "reminder_escalation_email", "manager@corp.test")

    def test_within_window_goes_to_assignee(self, db, users, make_line, fake_sender):
        make_line(due_in_days=-5, assigned_to=users["alice"])
        result = run_reminders(db, sender=fake_sender)

        assert result.emails_sent == 1
        assert result.emails_escalated == 0
        assert fake_sender.sent[0].to == "alice@corp.test"

    def test_past_window_goes_to_escalation_address(self, db, users, make_line, fake_sender):
        make_line(due_in_days=-9, assigned_to=users["alice"])
        result = run_reminders(db, sender=fake_sender)

        assert result.emails_sent == 1
        assert result.emails_escalated == 1
        assert fake_sender.sent[0].to == "manager@corp.test"
        assert fake_sender.sent[0].subject.startswith("[ESCALATED] ")

    def test_escalated_send_still_dedupes_once_per_day(self, db, users, make_line, fake_sender):
        make_line(due_in_days=-9, assigned_to=users["alice"])
        run_reminders(db, sender=fake_sender)
        second = run_reminders(db, sender=fake_sender)

        assert second.emails_sent == 0
        assert second.skipped_already_sent == 1
        assert len(fake_sender.sent) == 1

    def test_transition_from_assignee_to_escalation_across_days(
        self, db, users, make_line, fake_sender
    ):
        # -7 today (within window -> assignee), -8 tomorrow (past window -> escalation)
        line = make_line(due_in_days=0, assigned_to=users["alice"])
        line.promised_delivery = TODAY - timedelta(days=7)
        db.commit()

        run_reminders(db, sender=fake_sender, today=TODAY)
        run_reminders(db, sender=fake_sender, today=TODAY + timedelta(days=1))

        assert [m.to for m in fake_sender.sent] == ["alice@corp.test", "manager@corp.test"]
