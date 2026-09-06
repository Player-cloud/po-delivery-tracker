"""Login rate limiting, password policy, security headers (M7 hardening)."""

import pytest
from fastapi.testclient import TestClient

from app.core.limiter import limiter
from app.core.security import WeakPasswordError, validate_password_strength
from app.db.session import get_db
from app.main import app


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    limiter.reset()
    yield TestClient(app)
    app.dependency_overrides.clear()
    limiter.reset()


class TestPasswordPolicy:
    def test_rejects_short(self):
        with pytest.raises(WeakPasswordError):
            validate_password_strength("short1")

    def test_rejects_repetitive(self):
        with pytest.raises(WeakPasswordError):
            validate_password_strength("aaaaaaaaaaaa")

    def test_rejects_common(self):
        with pytest.raises(WeakPasswordError):
            validate_password_strength("password")

    def test_accepts_reasonable(self):
        validate_password_strength("Sup3rSecret!")  # no raise

    def test_create_user_endpoint_rejects_weak(self, client, db):
        from app.core.deps import get_current_user
        from app.models.user import User, UserRole

        admin = User(
            email="admin@corp.example", password_hash="x", role=UserRole.ADMINISTRATOR, active=True
        )
        db.add(admin)
        db.commit()
        app.dependency_overrides[get_current_user] = lambda: admin
        r = client.post(
            "/api/v1/users",
            json={"email": "x@corp.example", "password": "short", "role": "staff"},
        )
        assert r.status_code == 422


class TestLoginRateLimit:
    def test_caps_repeated_attempts(self, client):
        # default limit is 10/minute; the 11th+ attempt from one IP is throttled
        codes = [
            client.post(
                "/api/v1/auth/login", data={"username": "n@o.pe", "password": "x"}
            ).status_code
            for _ in range(13)
        ]
        assert codes[:10] == [401] * 10  # first 10 reach the auth check
        assert 429 in codes[10:], codes


class TestSecurityHeaders:
    def test_present_on_responses(self, client):
        r = client.get("/health")
        assert r.headers["x-content-type-options"] == "nosniff"
        assert r.headers["x-frame-options"] == "DENY"
        assert "referrer-policy" in r.headers
        assert "permissions-policy" in r.headers
