"""PO line attachments (M3, FR-4) — upload / list / download / delete + validation."""
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.crud import attachment as attachment_crud
from app.db.session import get_db
from app.main import app
from app.models.attachment import Attachment
from app.services import storage as storage_mod

settings = get_settings()


@pytest.fixture(autouse=True)
def _local_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "local_upload_dir", str(tmp_path))
    storage_mod.get_storage.cache_clear()
    yield
    storage_mod.get_storage.cache_clear()


@pytest.fixture
def client_as(db, users):
    def _as(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app)

    yield _as
    app.dependency_overrides.clear()


@pytest.fixture
def line(users, make_line):
    return make_line(due_in_days=10, assigned_to=users["alice"])


def _upload(client, line_id, name="invoice.pdf", content=b"%PDF-1.4 hello", ctype="application/pdf"):
    return client.post(
        f"/api/v1/po-lines/{line_id}/attachments",
        files={"file": (name, content, ctype)},
    )


class TestUpload:
    def test_upload_then_list_and_file_on_disk(self, client_as, users, line, tmp_path):
        c = client_as(users["alice"])
        r = _upload(c, line.id)
        assert r.status_code == 201
        body = r.json()
        assert body["file_name"] == "invoice.pdf"
        assert body["size_bytes"] == len(b"%PDF-1.4 hello")
        assert body["uploaded_by_id"] == users["alice"].id

        listed = c.get(f"/api/v1/po-lines/{line.id}/attachments").json()
        assert [a["id"] for a in listed] == [body["id"]]

        # the bytes really landed in local storage
        files = list(tmp_path.rglob("*"))
        assert any(f.is_file() and f.read_bytes() == b"%PDF-1.4 hello" for f in files)

    def test_rejects_disallowed_extension(self, client_as, users, line):
        r = _upload(client_as(users["alice"]), line.id, name="malware.exe", ctype="application/octet-stream")
        assert r.status_code == 400
        assert "not allowed" in r.json()["detail"]

    def test_rejects_oversized_file(self, client_as, users, line, monkeypatch):
        monkeypatch.setattr(settings, "attachment_max_bytes", 8)
        r = _upload(client_as(users["alice"]), line.id, content=b"123456789")
        assert r.status_code == 400
        assert "limit" in r.json()["detail"]

    def test_rejects_empty_file(self, client_as, users, line):
        r = _upload(client_as(users["alice"]), line.id, content=b"")
        assert r.status_code == 400

    def test_filename_is_sanitised(self, client_as, users, line, db):
        r = _upload(client_as(users["alice"]), line.id, name="../../etc/pa ss wd.txt", ctype="text/plain")
        assert r.status_code == 201
        row = db.get(Attachment, r.json()["id"])
        assert "/" not in row.file_name and "\\" not in row.file_name
        assert row.blob_path.startswith(f"po_lines/{line.id}/")


class TestDownload:
    def test_download_returns_bytes_and_filename(self, client_as, users, line):
        c = client_as(users["alice"])
        aid = _upload(c, line.id, content=b"%PDF-1.4 payload").json()["id"]
        r = c.get(f"/api/v1/po-lines/{line.id}/attachments/{aid}")
        assert r.status_code == 200
        assert r.content == b"%PDF-1.4 payload"
        assert "invoice.pdf" in r.headers["content-disposition"]

    def test_download_404_for_wrong_line(self, client_as, users, line, make_line):
        c = client_as(users["alice"])
        aid = _upload(c, line.id).json()["id"]
        other = make_line(due_in_days=5, assigned_to=users["alice"])
        assert c.get(f"/api/v1/po-lines/{other.id}/attachments/{aid}").status_code == 404


class TestDelete:
    def test_delete_removes_row_and_blob(self, client_as, users, line, db, tmp_path):
        c = client_as(users["alice"])
        aid = _upload(c, line.id).json()["id"]
        blob = db.get(Attachment, aid).blob_path

        assert c.delete(f"/api/v1/po-lines/{line.id}/attachments/{aid}").status_code == 204
        assert db.get(Attachment, aid) is None
        assert not (tmp_path / blob).exists()


class TestVisibility:
    def test_staff_cannot_touch_another_staffs_line(self, db, client_as, users, make_line):
        from app.models.user import User, UserRole

        carol = User(email="carol@corp.example", password_hash="x", role=UserRole.STAFF, active=True)
        db.add(carol)
        db.commit()

        line = make_line(due_in_days=10, assigned_to=users["alice"])  # alice's line

        r = client_as(carol).post(
            f"/api/v1/po-lines/{line.id}/attachments",
            files={"file": ("x.txt", b"hi", "text/plain")},
        )
        assert r.status_code == 403

    def test_cascade_delete_with_po_line(self, db, users, make_line):
        from app.crud.po_line import delete_po_line

        line = make_line(due_in_days=10, assigned_to=users["alice"])
        attachment_crud.create_attachment(
            db, line, file_name="a.txt", content_type="text/plain",
            data=b"bytes", uploader=users["alice"],
        )
        assert len(attachment_crud.list_attachments(db, line.id)) == 1

        delete_po_line(db, line)
        assert attachment_crud.list_attachments(db, line.id) == []
