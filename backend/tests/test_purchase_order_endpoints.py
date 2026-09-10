"""M8 Phase 2: /purchase-orders endpoints + PO-line list filters."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.po_line import DeliveryStatus
from app.models.user import User, UserRole

FUTURE = (date.today() + timedelta(days=15)).isoformat()
TODAY_ISO = date.today().isoformat()


@pytest.fixture
def manager(db):
    u = User(
        email="mgr@corp.example",
        full_name="Mary Manager",
        password_hash="x",
        role=UserRole.MANAGER,
        active=True,
    )
    db.add(u)
    db.commit()
    return u


@pytest.fixture
def client(db, manager):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: manager
    yield TestClient(app)
    app.dependency_overrides.clear()


def _add_line(client, manager, po_number, po_line, **over):
    body = {
        "po_number": po_number,
        "po_line": po_line,
        "quantity": over.get("quantity", 1),
        "issue_date": TODAY_ISO,
        "promised_delivery": over.get("promised_delivery", FUTURE),
        "assigned_to_id": manager.id,
    }
    r = client.post("/api/v1/po-lines", json=body)
    assert r.status_code == 201, r.text
    return r.json()


class TestPurchaseOrderCrud:
    def test_line_create_makes_a_po(self, client, manager):
        _add_line(client, manager, "PO-900", 1)
        pos = client.get("/api/v1/purchase-orders").json()
        assert [p["po_number"] for p in pos] == ["PO-900"]
        assert pos[0]["status"] == "open"
        assert pos[0]["line_count"] == 1

    def test_create_explicit_po_then_conflict(self, client):
        assert (
            client.post("/api/v1/purchase-orders", json={"po_number": "PO-901"}).status_code == 201
        )
        assert (
            client.post("/api/v1/purchase-orders", json={"po_number": "PO-901"}).status_code == 409
        )

    def test_detail_includes_lines(self, client, manager):
        _add_line(client, manager, "PO-902", 1)
        _add_line(client, manager, "PO-902", 2)
        po_id = client.get("/api/v1/purchase-orders").json()[0]["id"]
        detail = client.get(f"/api/v1/purchase-orders/{po_id}").json()
        assert detail["line_count"] == 2
        assert {line["po_line"] for line in detail["lines"]} == {1, 2}

    def test_detail_404_for_unknown(self, client):
        assert client.get("/api/v1/purchase-orders/99999").status_code == 404


class TestStatusTransitions:
    def _po_id(self, client):
        return client.get("/api/v1/purchase-orders").json()[0]["id"]

    def test_close_requires_delivered(self, client, manager):
        _add_line(client, manager, "PO-910", 1)
        po_id = self._po_id(client)
        # still open -> can't close
        assert (
            client.put(f"/api/v1/purchase-orders/{po_id}", json={"action": "close"}).status_code
            == 409
        )

        line_id = client.get(f"/api/v1/purchase-orders/{po_id}").json()["lines"][0]["id"]
        client.put(f"/api/v1/po-lines/{line_id}", json={"delivery_status": "complete"})
        assert client.get(f"/api/v1/purchase-orders/{po_id}").json()["status"] == "delivered"

        r = client.put(f"/api/v1/purchase-orders/{po_id}", json={"action": "close"})
        assert r.status_code == 200 and r.json()["status"] == "closed"

    def test_cancel_then_reopen(self, client, manager):
        _add_line(client, manager, "PO-911", 1)
        po_id = self._po_id(client)
        assert (
            client.put(f"/api/v1/purchase-orders/{po_id}", json={"action": "cancel"}).json()[
                "status"
            ]
            == "cancelled"
        )
        assert (
            client.put(f"/api/v1/purchase-orders/{po_id}", json={"action": "reopen"}).json()[
                "status"
            ]
            == "open"
        )

    def test_cannot_add_line_to_closed_po(self, client, manager):
        _add_line(client, manager, "PO-912", 1)
        po_id = self._po_id(client)
        line_id = client.get(f"/api/v1/purchase-orders/{po_id}").json()["lines"][0]["id"]
        client.put(f"/api/v1/po-lines/{line_id}", json={"delivery_status": "complete"})
        client.put(f"/api/v1/purchase-orders/{po_id}", json={"action": "close"})

        body = {
            "po_number": "PO-912",
            "po_line": 2,
            "quantity": 1,
            "issue_date": TODAY_ISO,
            "promised_delivery": FUTURE,
            "assigned_to_id": manager.id,
        }
        assert client.post("/api/v1/po-lines", json=body).status_code == 409


class TestStaffCannotTransition:
    def test_staff_gets_403(self, db, manager):
        staff = User(email="s@corp.example", password_hash="x", role=UserRole.STAFF, active=True)
        db.add(staff)
        db.commit()
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: staff
        c = TestClient(app)
        try:
            c.post(
                "/api/v1/po-lines",
                json={
                    "po_number": "PO-913",
                    "po_line": 1,
                    "quantity": 1,
                    "issue_date": TODAY_ISO,
                    "promised_delivery": FUTURE,
                    "assigned_to_id": staff.id,
                },
            )
            po_id = c.get("/api/v1/purchase-orders").json()[0]["id"]
            assert (
                c.put(f"/api/v1/purchase-orders/{po_id}", json={"action": "cancel"}).status_code
                == 403
            )
        finally:
            app.dependency_overrides.clear()


class TestLineFilters:
    def test_due_within_and_delivery_status(self, client, manager):
        _add_line(
            client,
            manager,
            "PO-920",
            1,
            promised_delivery=(date.today() + timedelta(days=5)).isoformat(),
        )
        _add_line(
            client,
            manager,
            "PO-921",
            1,
            promised_delivery=(date.today() + timedelta(days=60)).isoformat(),
        )
        near = client.get("/api/v1/po-lines?due_within=30").json()
        assert {l["po_number"] for l in near} == {"PO-920"}

        line_id = near[0]["id"]
        client.put(f"/api/v1/po-lines/{line_id}", json={"delivery_status": "partial"})
        partial = client.get("/api/v1/po-lines?delivery_status=partial").json()
        assert [l["po_number"] for l in partial] == ["PO-920"]
        assert partial[0]["delivery_status"] == DeliveryStatus.PARTIAL.value

    def test_po_status_filter(self, client, manager):
        # PO-930: single line, mark it complete -> PO auto-Delivered
        line = _add_line(client, manager, "PO-930", 1)
        client.put(f"/api/v1/po-lines/{line['id']}", json={"delivery_status": "complete"})
        _add_line(client, manager, "PO-931", 1)  # stays open

        delivered = client.get("/api/v1/po-lines?po_status=delivered").json()
        assert {l["po_number"] for l in delivered} == {"PO-930"}
        open_lines = client.get("/api/v1/po-lines?po_status=open").json()
        assert {l["po_number"] for l in open_lines} == {"PO-931"}

    def test_search_matches_po_number_or_line(self, client, manager):
        _add_line(client, manager, "PO-940", 1)
        _add_line(client, manager, "PO-940", 2)
        _add_line(client, manager, "PO-941", 2)

        by_po = client.get("/api/v1/po-lines?search=PO-940").json()
        assert {(l["po_number"], l["po_line"]) for l in by_po} == {("PO-940", 1), ("PO-940", 2)}

        by_line = client.get("/api/v1/po-lines?search=2").json()
        assert {(l["po_number"], l["po_line"]) for l in by_line} == {
            ("PO-940", 2),
            ("PO-941", 2),
        }
