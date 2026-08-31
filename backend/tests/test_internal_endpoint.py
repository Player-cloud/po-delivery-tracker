"""Auth + wiring tests for POST /api/v1/internal/run-reminders."""
import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints import internal
from app.db.session import get_db
from app.main import app

SECRET = "test-cron-secret"


@pytest.fixture
def client(db, monkeypatch):
    monkeypatch.setattr(internal.settings, "cron_secret", SECRET)
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_rejects_missing_authorization(client):
    assert client.post("/api/v1/internal/run-reminders").status_code == 401


def test_rejects_wrong_secret(client):
    r = client.post(
        "/api/v1/internal/run-reminders",
        headers={"Authorization": "Bearer nope"},
    )
    assert r.status_code == 401


def test_accepts_correct_secret_and_returns_run_summary(client):
    r = client.post(
        "/api/v1/internal/run-reminders",
        headers={"Authorization": f"Bearer {SECRET}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["lines_scanned"] == 0
    assert body["emails_sent"] == 0
    assert "thresholds_days" in body
