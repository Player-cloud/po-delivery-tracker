"""
The model registry: imports every model so Alembic's autogenerate (and
anything else that needs the full picture, like app startup) sees every
table via Base.metadata.

This file is safe to import models into, because it only re-exports Base
(from base_class.py) rather than defining it — nothing imports *from* this
file to get Base, so there's no cycle. Models themselves import Base from
app.db.base_class directly, never from here.
"""

from app.db.base_class import Base  # noqa: F401 — re-exported for convenience
from app.models.attachment import Attachment  # noqa: F401
from app.models.configuration import Configuration  # noqa: F401
from app.models.deletion_request import DeletionRequest  # noqa: F401
from app.models.notification_history import NotificationHistory  # noqa: F401
from app.models.po_line import POLine  # noqa: F401
from app.models.user import User  # noqa: F401
