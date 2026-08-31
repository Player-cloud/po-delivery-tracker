"""Test fixtures.

`db` is an isolated SQLite database with the full schema and a couple of users.
SQLite is close enough for the reminder engine: the engine only reads `delivered`
and does date math in Python, so the Postgres-specific bits (generated
`lead_time_days`, SQL `days_remaining` expression) are never exercised here.
"""

from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.po_line import POLine, Priority
from app.models.user import User, UserRole


@pytest.fixture
def db():
    # StaticPool + one shared connection so the same in-memory DB is visible from
    # the TestClient's worker thread as well as the test thread.
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, future=True)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def users(db):
    alice = User(email="alice@corp.test", password_hash="x", role=UserRole.STAFF, active=True)
    bob = User(email="bob@corp.test", password_hash="x", role=UserRole.STAFF, active=False)
    db.add_all([alice, bob])
    db.commit()
    return {"alice": alice, "bob": bob}


_DEFAULT = object()


@pytest.fixture
def make_line(db, users):
    counter = {"n": 0}

    def _make(*, due_in_days: int, delivered: bool = False, assigned_to=_DEFAULT, po_number=None):
        # Assigned To is required (PRD §14 Q2) — default to an active user.
        assignee = users["alice"] if assigned_to is _DEFAULT else assigned_to
        counter["n"] += 1
        line = POLine(
            po_number=po_number or f"PO{counter['n']:03d}",
            po_line=1,
            issue_date=date.today() - timedelta(days=30),
            promised_delivery=date.today() + timedelta(days=due_in_days),
            delivered=delivered,
            priority=Priority.MEDIUM,
            assigned_to_id=assignee.id if assignee is not None else None,
        )
        db.add(line)
        db.commit()
        return line

    return _make


class FakeSender:
    """Captures messages instead of sending. `fail_for` = set of recipient
    addresses that should raise, to exercise the per-line error path."""

    def __init__(self, fail_for: set[str] | None = None):
        self.sent: list = []
        self.fail_for = fail_for or set()

    def send(self, message):
        from app.services.notifications import NotificationError

        if message.to in self.fail_for:
            raise NotificationError(f"simulated failure for {message.to}")
        self.sent.append(message)


@pytest.fixture
def fake_sender():
    return FakeSender()
