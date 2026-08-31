"""Factory: turn `settings.email_backend` into a concrete NotificationSender."""
from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.services.notifications.base import (
    EmailMessage,
    NotificationError,
    NotificationSender,
)

__all__ = [
    "EmailMessage",
    "NotificationError",
    "NotificationSender",
    "get_notification_sender",
]


@lru_cache
def get_notification_sender() -> NotificationSender:
    backend = get_settings().email_backend.lower()

    if backend == "smtp":
        from app.services.notifications.smtp import SMTPNotificationSender

        return SMTPNotificationSender()
    if backend == "resend":
        from app.services.notifications.resend import ResendNotificationSender

        return ResendNotificationSender()
    if backend == "brevo":
        from app.services.notifications.brevo import BrevoNotificationSender

        return BrevoNotificationSender()

    raise NotificationError(
        f"Unknown EMAIL_BACKEND {backend!r} — expected one of: smtp, resend, brevo"
    )
