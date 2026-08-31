"""Assigned To is a required field (PRD §14 Q2): schema-level and CRUD-level checks."""

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.crud import po_line as po_line_crud
from app.crud.po_line import InvalidAssigneeError
from app.models.user import User, UserRole
from app.schemas.po_line import POLineCreate, POLineUpdate

FUTURE = (date.today() + timedelta(days=30)).isoformat()
TODAY_ISO = date.today().isoformat()


class TestSchema:
    def _base(self, **over):
        return {
            "po_number": "PO1",
            "po_line": 1,
            "issue_date": TODAY_ISO,
            "promised_delivery": FUTURE,
            "assigned_to_id": 1,
            **over,
        }

    def test_create_requires_assigned_to_id(self):
        payload = self._base()
        payload.pop("assigned_to_id")
        with pytest.raises(ValidationError):
            POLineCreate(**payload)

    def test_create_accepts_assigned_to_id(self):
        assert POLineCreate(**self._base(assigned_to_id=5)).assigned_to_id == 5

    def test_update_may_omit_assignee(self):
        assert POLineUpdate(notes="x").model_dump(exclude_unset=True) == {"notes": "x"}

    def test_update_may_reassign(self):
        assert POLineUpdate(assigned_to_id=9).assigned_to_id == 9

    def test_update_rejects_explicit_null_assignee(self):
        with pytest.raises(ValidationError):
            POLineUpdate(assigned_to_id=None)


class TestCrudValidation:
    @pytest.fixture
    def active_user(self, db):
        u = User(email="act@corp.test", password_hash="x", role=UserRole.STAFF, active=True)
        db.add(u)
        db.commit()
        return u

    @pytest.fixture
    def inactive_user(self, db):
        u = User(email="ina@corp.test", password_hash="x", role=UserRole.STAFF, active=False)
        db.add(u)
        db.commit()
        return u

    def _create(self, db, user, assigned_to_id):
        data = POLineCreate(
            po_number="POX",
            po_line=1,
            issue_date=TODAY_ISO,
            promised_delivery=FUTURE,
            assigned_to_id=assigned_to_id,
        )
        return po_line_crud.create_po_line(db, data, user)

    def test_create_with_valid_active_assignee(self, db, active_user):
        line = self._create(db, active_user, active_user.id)
        assert line.assigned_to_id == active_user.id

    def test_create_rejects_unknown_assignee(self, db, active_user):
        with pytest.raises(InvalidAssigneeError):
            self._create(db, active_user, 999999)

    def test_create_rejects_inactive_assignee(self, db, active_user, inactive_user):
        with pytest.raises(InvalidAssigneeError):
            self._create(db, active_user, inactive_user.id)

    def test_update_rejects_inactive_assignee(self, db, active_user, inactive_user):
        line = self._create(db, active_user, active_user.id)
        with pytest.raises(InvalidAssigneeError):
            po_line_crud.update_po_line(
                db, line, POLineUpdate(assigned_to_id=inactive_user.id), active_user
            )
