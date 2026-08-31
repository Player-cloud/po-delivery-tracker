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

# noqa: F401 — imported for side effect (registering tables on Base.metadata)
from app.models.user import User  # noqa: E402, F401
from app.models.po_line import POLine  # noqa: E402, F401
from app.models.attachment import Attachment  # noqa: E402, F401
from app.models.notification_history import NotificationHistory  # noqa: E402, F401
from app.models.configuration import Configuration  # noqa: E402, F401
from app.models.deletion_request import DeletionRequest  # noqa: E402, F401
