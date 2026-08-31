"""Admin user management (M4) — create/list/update + the lockout guards."""

import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole


@pytest.fixture
def admin(db):
    u = User(
        email="admin@corp.example", password_hash="x", role=UserRole.ADMINISTRATOR, active=True
    )
    db.add(u)
    db.commit()
    return u


@pytest.fixture
def client(db, admin):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: admin
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_list_and_update_user(client, db):
    r = client.post(
        "/api/v1/users",
        json={"email": "new@corp.example", "password": "secret123", "role": "staff"},
    )
    assert r.status_code == 201
    uid = r.json()["id"]

    emails = [u["email"] for u in client.get("/api/v1/users").json()]
    assert "new@corp.example" in emails

    r = client.put(f"/api/v1/users/{uid}", json={"role": "manager", "active": False})
    assert r.status_code == 200
    assert r.json()["role"] == "manager" and r.json()["active"] is False


def test_duplicate_email_rejected(client):
    body = {"email": "dup@corp.example", "password": "secret123", "role": "viewer"}
    assert client.post("/api/v1/users", json=body).status_code == 201
    assert client.post("/api/v1/users", json=body).status_code == 409


def test_admin_cannot_demote_self(client, admin):
    r = client.put(f"/api/v1/users/{admin.id}", json={"role": "manager"})
    assert r.status_code == 400
    assert "your own" in r.json()["detail"]


def test_admin_cannot_deactivate_self(client, admin):
    assert client.put(f"/api/v1/users/{admin.id}", json={"active": False}).status_code == 400


def test_admin_may_demote_a_different_admin(client, db):
    other = User(
        email="other-admin@corp.example",
        password_hash="x",
        role=UserRole.ADMINISTRATOR,
        active=True,
    )
    db.add(other)
    db.commit()
    # the acting admin (fixture) stays, so this is allowed
    r = client.put(f"/api/v1/users/{other.id}", json={"role": "staff"})
    assert r.status_code == 200
    assert r.json()["role"] == "staff"


def test_admin_may_still_change_own_password(client, admin):
    assert (
        client.put(f"/api/v1/users/{admin.id}", json={"password": "newsecret123"}).status_code
        == 200
    )
