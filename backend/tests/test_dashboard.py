"""Dashboard summary partition + /dashboard/attention (M2, FR-15/FR-16)."""
import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.crud.po_line import attention_lines, dashboard_summary
from app.db.session import get_db
from app.main import app


@pytest.fixture
def client(db, users):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: users["alice"]
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def spread(users, make_line):
    """A line in every urgency bucket, plus a delivered one."""
    a = users["alice"]
    return {
        "overdue": make_line(due_in_days=-3, assigned_to=a),
        "today": make_line(due_in_days=0, assigned_to=a),
        "soon": make_line(due_in_days=4, assigned_to=a),
        "later": make_line(due_in_days=40, assigned_to=a),
        "done": make_line(due_in_days=-10, delivered=True, assigned_to=a),
    }


class TestSummary:
    def test_buckets_partition_total_open(self, db, users, spread):
        s = dashboard_summary(db, users["alice"])
        assert s["total_open"] == 4
        assert s["overdue"] + s["due_today"] + s["due_soon"] + s["later"] == s["total_open"]
        assert (s["overdue"], s["due_today"], s["due_soon"], s["later"]) == (1, 1, 1, 1)
        assert s["completed"] == 1

    def test_due_this_week_still_includes_today(self, db, users, spread):
        s = dashboard_summary(db, users["alice"])
        assert s["due_this_week"] == 2  # today + the 4-days-out line

    def test_summary_endpoint_shape(self, client):
        body = client.get("/api/v1/dashboard/summary").json()
        assert set(body) == {
            "total_open", "due_today", "due_this_week", "due_soon",
            "later", "overdue", "completed", "high_priority",
        }


class TestAttention:
    def test_only_open_lines_within_a_week_or_overdue(self, db, users, spread):
        lines = attention_lines(db, users["alice"])
        nums = {l.po_number for l in lines}
        assert spread["overdue"].po_number in nums
        assert spread["today"].po_number in nums
        assert spread["soon"].po_number in nums
        assert spread["later"].po_number not in nums   # 40 days out
        assert spread["done"].po_number not in nums     # delivered

    def test_ordered_most_urgent_first(self, db, users, make_line):
        a = users["alice"]
        make_line(due_in_days=5, assigned_to=a)
        make_line(due_in_days=-8, assigned_to=a)
        make_line(due_in_days=0, assigned_to=a)

        remaining = [l.days_remaining for l in attention_lines(db, a)]
        assert remaining == sorted(remaining)
        assert remaining[0] == -8

    def test_respects_limit(self, db, users, make_line):
        a = users["alice"]
        for _ in range(8):
            make_line(due_in_days=2, assigned_to=a)
        assert len(attention_lines(db, a, limit=3)) == 3

    def test_staff_only_sees_own_lines(self, db, users, make_line):
        make_line(due_in_days=1, assigned_to=users["alice"])
        make_line(due_in_days=1, assigned_to=users["bob"])
        # alice is STAFF -> assigned-only visibility
        lines = attention_lines(db, users["alice"])
        assert len(lines) == 1
        assert lines[0].assigned_to_id == users["alice"].id

    def test_endpoint_returns_po_line_shape(self, client, spread):
        rows = client.get("/api/v1/dashboard/attention").json()
        assert rows and {"days_remaining", "status", "po_number", "assigned_to_id"} <= set(rows[0])
