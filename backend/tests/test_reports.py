"""M8 Phase 4: /reports — report data, filters, and CSV/XLSX/PDF export."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.po_line import DeliveryStatus
from app.models.user import User, UserRole
from app.services import reports
from app.services.report_formats import render


@pytest.fixture
def viewer_user(db):
    # Reports are visible to everyone; run them as a Viewer so the visibility
    # rules don't hide half the dataset (Viewer sees all lines, like Manager).
    u = User(
        email="rep@corp.test",
        full_name="Rae Report",
        password_hash="x",
        role=UserRole.VIEWER,
        active=True,
    )
    db.add(u)
    db.commit()
    return u


@pytest.fixture
def client(db, viewer_user):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: viewer_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def dataset(db, users, make_line):
    a, b = users["alice"], users["bob"]
    # two overdue, not delivered
    make_line(due_in_days=-5, assigned_to=a)
    make_line(due_in_days=-1, assigned_to=a)
    # delivered on time (promised +10d, delivered "now" which is < promised)
    make_line(
        due_in_days=10,
        delivery_status=DeliveryStatus.COMPLETE,
        delivered_at=datetime.now(UTC),
        assigned_to=a,
    )
    # delivered late (promised 3 days ago, delivered now)
    make_line(
        due_in_days=-3,
        delivery_status=DeliveryStatus.COMPLETE,
        delivered_at=datetime.now(UTC),
        assigned_to=b,
    )
    # partial, future
    make_line(due_in_days=20, delivery_status=DeliveryStatus.PARTIAL, assigned_to=b)


def test_list_reports(client):
    names = {r["name"] for r in client.get("/api/v1/reports").json()}
    assert names == {"all_lines", "overdue", "deliveries", "on_time", "by_assignee", "by_status"}


class TestAllLines:
    def test_includes_every_visible_line(self, client, dataset):
        body = client.get("/api/v1/reports/all_lines").json()
        assert body["summary"]["count"] == 5  # the whole dataset

    def test_po_status_filter(self, client, dataset):
        # each make_line gets its own PO; the two complete lines -> two Delivered POs
        delivered = client.get("/api/v1/reports/all_lines?po_status=delivered").json()
        assert delivered["summary"]["count"] == 2
        assert all(r["po_status"] == "Delivered" for r in delivered["rows"])
        pending = client.get("/api/v1/reports/all_lines?po_status=open").json()
        assert pending["summary"]["count"] == 3


class TestOverdue:
    def test_only_open_and_past_due(self, client, dataset):
        body = client.get("/api/v1/reports/overdue").json()
        assert body["summary"]["count"] == 2
        assert all(r["days_overdue"] >= 1 for r in body["rows"])
        assert body["rows"][0]["days_overdue"] >= body["rows"][-1]["days_overdue"]  # sorted desc


class TestDeliveries:
    def test_on_time_flag_and_summary(self, client, dataset):
        body = client.get("/api/v1/reports/deliveries").json()
        assert body["summary"]["count"] == 2
        assert body["summary"]["on_time"] == 1
        assert body["summary"]["late"] == 1
        assert body["summary"]["on_time_pct"] == 50.0

    def test_date_range_filter(self, client, dataset):
        future = (datetime.now(UTC) + timedelta(days=1)).date().isoformat()
        body = client.get(f"/api/v1/reports/deliveries?from={future}").json()
        assert body["summary"]["count"] == 0


class TestOnTime:
    def test_breakdown_by_assignee(self, client, dataset):
        body = client.get("/api/v1/reports/on_time").json()
        assert body["summary"]["delivered"] == 2
        assert body["summary"]["on_time_pct"] == 50.0
        by = {r["assignee"]: r for r in body["rows"]}
        assert by["Alice Adams"]["on_time"] == 1
        assert by["Bob Barnes"]["late"] == 1


class TestByAssigneeAndStatus:
    def test_by_assignee(self, client, dataset):
        rows = {r["assignee"]: r for r in client.get("/api/v1/reports/by_assignee").json()["rows"]}
        assert rows["Alice Adams"]["total"] == 3
        assert rows["Alice Adams"]["overdue"] == 2
        assert rows["Bob Barnes"]["partial"] == 1

    def test_by_status(self, client, dataset):
        rows = {
            r["delivery_status"]: r for r in client.get("/api/v1/reports/by_status").json()["rows"]
        }
        assert rows["Not Delivered"]["lines"] == 2
        assert rows["Complete"]["lines"] == 2
        assert rows["Partial"]["lines"] == 1


class TestFilters:
    def test_assignee_filter(self, client, dataset, users):
        body = client.get(f"/api/v1/reports/by_status?assignee_id={users['bob'].id}").json()
        rows = {r["delivery_status"]: r["lines"] for r in body["rows"]}
        assert rows["Partial"] == 1 and rows["Not Delivered"] == 0


class TestExportFormats:
    @pytest.mark.parametrize("fmt", ["csv", "xlsx", "pdf"])
    def test_download(self, client, dataset, fmt):
        r = client.get(f"/api/v1/reports/deliveries?format={fmt}")
        assert r.status_code == 200
        assert len(r.content) > 100
        assert "attachment" in r.headers["content-disposition"]
        assert f".{fmt}" in r.headers["content-disposition"]

    def test_pdf_magic_bytes(self, client, dataset):
        r = client.get("/api/v1/reports/on_time?format=pdf")
        assert r.content[:4] == b"%PDF"

    def test_xlsx_is_a_zip(self, client, dataset):
        r = client.get("/api/v1/reports/overdue?format=xlsx")
        assert r.content[:2] == b"PK"

    def test_render_helper_directly(self, db, users):
        report = reports.build(db, users["alice"], "by_status", reports.ReportFilters())
        assert render(report, "csv").startswith(b"\xef\xbb\xbf")  # UTF-8 BOM


def test_unknown_report_404(client):
    assert client.get("/api/v1/reports/nope").status_code == 404


def test_viewer_can_run_reports(db):
    viewer = User(
        email="v@corp.test",
        full_name="Vic Viewer",
        password_hash="x",
        role=UserRole.VIEWER,
        active=True,
    )
    db.add(viewer)
    db.commit()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: viewer
    try:
        r = TestClient(app).get("/api/v1/reports/by_status?format=csv")
        assert r.status_code == 200
    finally:
        app.dependency_overrides.clear()
