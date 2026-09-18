"""Forgot-password flow: emailed one-time link -> new password -> login."""

import hashlib
import re
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.v1.endpoints import auth as auth_endpoints
from app.core.limiter import limiter
from app.core.security import hash_password
from app.db.session import get_db
from app.main import app
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User, UserRole

OLD_PW = "Old-password-123"
NEW_PW = "Brand-new-pass-99"


@pytest.fixture
def ese(db):
    u = User(
        email="ese@corp.example",
        full_name="Ese Okoro",
        password_hash=hash_password(OLD_PW),
        role=UserRole.ADMINISTRATOR,
        active=True,
    )
    db.add(u)
    db.commit()
    return u


@pytest.fixture
def client(db, fake_sender, monkeypatch):
    app.dependency_overrides[get_db] = lambda: db
    monkeypatch.setattr(auth_endpoints, "get_notification_sender", lambda: fake_sender)
    limiter.reset()
    yield TestClient(app)
    app.dependency_overrides.clear()
    limiter.reset()


def _forgot(client, email="ese@corp.example"):
    return client.post("/api/v1/auth/forgot-password", json={"email": email})


def _token_from(message) -> str:
    m = re.search(r"/reset-password\?token=([\w-]+)", message.text_body)
    assert m, message.text_body
    return m.group(1)


def _login(client, email, pw):
    return client.post("/api/v1/auth/login", data={"username": email, "password": pw})


def test_forgot_emails_a_link_and_stores_only_the_hash(client, db, ese, fake_sender):
    r = _forgot(client)
    assert r.status_code == 202

    assert len(fake_sender.sent) == 1
    msg = fake_sender.sent[0]
    assert msg.to == "ese@corp.example"
    assert msg.text_body.startswith("Hi Ese,")
    raw = _token_from(msg)

    row = db.scalar(select(PasswordResetToken))
    assert row.user_id == ese.id
    assert row.token_hash == hashlib.sha256(raw.encode()).hexdigest()
    assert raw not in row.token_hash  # the raw token is never stored


def test_unknown_email_gets_the_same_reply_and_no_mail(client, db, ese, fake_sender):
    known = _forgot(client)
    unknown = _forgot(client, "nobody@corp.example")
    assert unknown.status_code == known.status_code == 202
    assert unknown.json() == known.json()
    assert [m.to for m in fake_sender.sent] == ["ese@corp.example"]


def test_disabled_account_gets_no_mail(client, db, ese, fake_sender):
    ese.active = False
    db.commit()
    assert _forgot(client).status_code == 202
    assert fake_sender.sent == []
    assert db.scalar(select(PasswordResetToken)) is None


def test_email_lookup_ignores_case(client, fake_sender, ese):
    assert _forgot(client, "Ese@Corp.Example").status_code == 202
    assert len(fake_sender.sent) == 1


def test_second_request_within_a_minute_sends_nothing_new(client, fake_sender, ese):
    _forgot(client)
    assert _forgot(client).status_code == 202
    assert len(fake_sender.sent) == 1


def test_a_newer_link_replaces_the_older_one(client, db, fake_sender, ese):
    _forgot(client)
    first = _token_from(fake_sender.sent[0])
    for row in db.scalars(select(PasswordResetToken)):  # age it past the throttle
        row.created_at = datetime.now(UTC) - timedelta(minutes=5)
    db.commit()

    _forgot(client)
    second = _token_from(fake_sender.sent[1])
    assert first != second

    def reset(tok):
        return client.post("/api/v1/auth/reset-password", json={"token": tok, "password": NEW_PW})

    assert reset(first).status_code == 400
    assert reset(second).status_code == 200


def test_reset_sets_the_new_password_once(client, fake_sender, ese):
    _forgot(client)
    tok = _token_from(fake_sender.sent[0])

    r = client.post("/api/v1/auth/reset-password", json={"token": tok, "password": NEW_PW})
    assert r.status_code == 200

    assert _login(client, "ese@corp.example", NEW_PW).status_code == 200
    assert _login(client, "ese@corp.example", OLD_PW).status_code == 401

    again = client.post("/api/v1/auth/reset-password", json={"token": tok, "password": NEW_PW})
    assert again.status_code == 400  # single use


def test_expired_link_is_rejected(client, db, fake_sender, ese):
    _forgot(client)
    tok = _token_from(fake_sender.sent[0])
    row = db.scalar(select(PasswordResetToken))
    row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()

    r = client.post("/api/v1/auth/reset-password", json={"token": tok, "password": NEW_PW})
    assert r.status_code == 400
    assert _login(client, "ese@corp.example", OLD_PW).status_code == 200


def test_garbage_token_is_rejected(client, ese):
    r = client.post("/api/v1/auth/reset-password", json={"token": "nope", "password": NEW_PW})
    assert r.status_code == 400


def test_weak_password_is_422_and_does_not_burn_the_link(client, fake_sender, ese):
    _forgot(client)
    tok = _token_from(fake_sender.sent[0])

    weak = client.post("/api/v1/auth/reset-password", json={"token": tok, "password": "short"})
    assert weak.status_code == 422

    ok = client.post("/api/v1/auth/reset-password", json={"token": tok, "password": NEW_PW})
    assert ok.status_code == 200


def test_account_disabled_after_request_cannot_reset(client, db, fake_sender, ese):
    _forgot(client)
    tok = _token_from(fake_sender.sent[0])
    ese.active = False
    db.commit()

    r = client.post("/api/v1/auth/reset-password", json={"token": tok, "password": NEW_PW})
    assert r.status_code == 400


def test_mail_failure_is_swallowed(client, ese, monkeypatch):
    def boom():
        raise RuntimeError("provider down")

    monkeypatch.setattr(auth_endpoints, "get_notification_sender", boom)
    assert _forgot(client).status_code == 202


def test_forgot_password_is_rate_limited(client):
    codes = [_forgot(client, f"x{i}@corp.example").status_code for i in range(7)]
    assert codes[:5] == [202] * 5
    assert 429 in codes[5:]


def test_login_email_is_case_insensitive(client, ese):
    assert _login(client, "ESE@corp.example", OLD_PW).status_code == 200
