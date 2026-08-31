"""GET /users/assignable — the picker feed for the PO line 'Assigned To' field."""
import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole


@pytest.fixture
def seeded(db):
    active_staff = User(email="s@corp.test", password_hash="x", role=UserRole.STAFF, active=True)
    active_mgr = User(email="m@corp.test", password_hash="x", role=UserRole.MANAGER, active=True)
    inactive = User(email="z@corp.test", password_hash="x", role=UserRole.STAFF, active=False)
    db.add_all([active_staff, active_mgr, inactive])
    db.commit()
    return {"staff": active_staff, "mgr": active_mgr, "inactive": inactive}


@pytest.fixture
def client_as(db, seeded):
    def _as(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app)

    yield _as
    app.dependency_overrides.clear()


def test_staff_can_list_assignable_users(client_as, seeded):
    r = client_as(seeded["staff"]).get("/api/v1/users/assignable")
    assert r.status_code == 200
    emails = [u["email"] for u in r.json()]
    assert "s@corp.test" in emails and "m@corp.test" in emails
    assert "z@corp.test" not in emails  # inactive excluded
    assert set(r.json()[0].keys()) == {"id", "email"}  # no role / status leaked


def test_viewer_is_forbidden(client_as, db):
    viewer = User(email="v@corp.test", password_hash="x", role=UserRole.VIEWER, active=True)
    db.add(viewer)
    db.commit()
    assert client_as(viewer).get("/api/v1/users/assignable").status_code == 403
