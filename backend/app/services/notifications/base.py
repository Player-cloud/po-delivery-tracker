"""
The `NotificationSender` interface.

The reminder engine (`app.services.reminders`) only ever talks to this abstract
class, so the same scheduler logic runs unchanged in every environment (PRD §10):

- local dev  -> `SMTPNotificationSender` pointed at Mailhog
- production -> `ResendNotificationSender` or `BrevoNotificationSender`

Pick one with `app.services.notifications.get_notification_sender()`, which reads
`settings.email_backend`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class NotificationError(Exception):
    """Raised when a message could not be handed off to the email provider.

    The reminder engine catches this per-line: the failing line is counted as an
    error and left with no NotificationHistory row, so the next daily run retries
    it. It never aborts the whole pass.
    """


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    text_body: str
    html_body: str | None = None


class NotificationSender(ABC):
    @abstractmethod
    def send(self, message: EmailMessage) -> None:
        """Deliver one message, or raise NotificationError. Must be synchronous."""
