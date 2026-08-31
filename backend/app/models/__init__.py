"""
Importing ANY model (e.g. `from app.models.po_line import POLine`) runs this
file first, since Python always executes a package's __init__.py before a
submodule inside it. By importing every model here, we guarantee all of them
are registered with SQLAlchemy before any relationship() gets resolved —
without this, `from app.models.po_line import POLine` alone would leave
"User" (referenced only by name/string inside POLine, to avoid a circular
import with user.py) unregistered, and the first POLine(...) you construct
would fail to resolve it.
"""
from app.models.user import User  # noqa: F401
from app.models.po_line import POLine  # noqa: F401
from app.models.attachment import Attachment  # noqa: F401
from app.models.notification_history import NotificationHistory  # noqa: F401
from app.models.configuration import Configuration  # noqa: F401
from app.models.deletion_request import DeletionRequest  # noqa: F401
