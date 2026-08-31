"""SMTP sender — used in local dev against Mailhog (see docker-compose.yml).

Deliberately uses the stdlib `smtplib` and no auth/TLS: Mailhog accepts anything
on port 1025 and never actually delivers, so you can watch reminders arrive at
http://localhost:8025 without sending real email.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage as MIMEEmailMessage

from app.core.config import get_settings
from app.services.notifications.base import EmailMessage, NotificationError, NotificationSender

settings = get_settings()


class SMTPNotificationSender(NotificationSender):
    def __init__(self, host: str | None = None, port: int | None = None) -> None:
        self._host = host or settings.smtp_host
        self._port = port or settings.smtp_port

    def send(self, message: EmailMessage) -> None:
        mime = MIMEEmailMessage()
        mime["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_address}>"
        mime["To"] = message.to
        mime["Subject"] = message.subject
        mime.set_content(message.text_body)
        if message.html_body:
            mime.add_alternative(message.html_body, subtype="html")

        try:
            with smtplib.SMTP(self._host, self._port, timeout=10) as smtp:
                smtp.send_message(mime)
        except (smtplib.SMTPException, OSError) as exc:
            raise NotificationError(f"SMTP send to {message.to} failed: {exc}") from exc
