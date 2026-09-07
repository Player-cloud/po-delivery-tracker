"""M8 Phase 1: PurchaseOrder entity, get-or-create, auto delivered status."""

from datetime import date, timedelta

from app.crud import po_line as po_line_crud
from app.crud.purchase_order import get_by_number, list_purchase_orders
from app.models.po_line import DeliveryStatus
from app.models.purchase_order import PurchaseOrderStatus
from app.schemas.po_line import POLineCreate, POLineUpdate

FUTURE = (date.today() + timedelta(days=20)).isoformat()
TODAY_ISO = date.today().isoformat()


def _line(db, user, *, po_number, po_line, qty=1):
    return po_line_crud.create_po_line(
        db,
        POLineCreate(
            po_number=po_number,
            po_line=po_line,
            quantity=qty,
            issue_date=TODAY_ISO,
            promised_delivery=FUTURE,
            assigned_to_id=user.id,
        ),
        user,
    )


class TestGetOrCreate:
    def test_two_lines_same_number_share_one_po(self, db, users):
        alice = users["alice"]
        a = _line(db, alice, po_number="PO-500", po_line=1)
        b = _line(db, alice, po_number="PO-500", po_line=2)
        assert a.purchase_order_id == b.purchase_order_id
        assert len(list_purchase_orders(db, alice)) == 1

    def test_duplicate_line_number_within_po_is_rejected(self, db, users):
        alice = users["alice"]
        _line(db, alice, po_number="PO-501", po_line=1)
        try:
            _line(db, alice, po_number="PO-501", po_line=1)
            raise AssertionError("expected DuplicatePOLineError")
        except po_line_crud.DuplicatePOLineError:
            pass

    def test_quantity_stored(self, db, users):
        line = _line(db, users["alice"], po_number="PO-502", po_line=1, qty=7)
        assert line.quantity == 7


class TestAutoStatus:
    def test_po_delivered_when_all_lines_complete(self, db, users):
        alice = users["alice"]
        a = _line(db, alice, po_number="PO-600", po_line=1)
        b = _line(db, alice, po_number="PO-600", po_line=2)
        po = get_by_number(db, "PO-600")
        assert po.status == PurchaseOrderStatus.OPEN

        po_line_crud.update_po_line(
            db, a, POLineUpdate(delivery_status=DeliveryStatus.COMPLETE), alice
        )
        assert get_by_number(db, "PO-600").status == PurchaseOrderStatus.OPEN  # b still open

        po_line_crud.update_po_line(
            db, b, POLineUpdate(delivery_status=DeliveryStatus.COMPLETE), alice
        )
        assert get_by_number(db, "PO-600").status == PurchaseOrderStatus.DELIVERED

    def test_reopening_a_line_reopens_the_po(self, db, users):
        alice = users["alice"]
        a = _line(db, alice, po_number="PO-601", po_line=1)
        po_line_crud.update_po_line(
            db, a, POLineUpdate(delivery_status=DeliveryStatus.COMPLETE), alice
        )
        assert get_by_number(db, "PO-601").status == PurchaseOrderStatus.DELIVERED
        po_line_crud.update_po_line(
            db, a, POLineUpdate(delivery_status=DeliveryStatus.PARTIAL), alice
        )
        assert get_by_number(db, "PO-601").status == PurchaseOrderStatus.OPEN

    def test_legacy_delivered_boolean_still_accepted(self, db, users):
        alice = users["alice"]
        a = _line(db, alice, po_number="PO-602", po_line=1)
        po_line_crud.update_po_line(db, a, POLineUpdate(delivered=True), alice)
        assert a.delivery_status == DeliveryStatus.COMPLETE
        assert get_by_number(db, "PO-602").status == PurchaseOrderStatus.DELIVERED


class TestDashboardCounts:
    def test_po_counts_in_summary(self, db, users):
        alice = users["alice"]
        _line(db, alice, po_number="PO-700", po_line=1)
        b = _line(db, alice, po_number="PO-701", po_line=1)
        po_line_crud.update_po_line(
            db, b, POLineUpdate(delivery_status=DeliveryStatus.COMPLETE), alice
        )
        s = po_line_crud.dashboard_summary(db, alice)
        assert s["total_pos"] == 2
        assert s["total_po_lines"] == 2
        assert s["pos_delivered"] == 1
        assert s["pos_closed"] == 0
