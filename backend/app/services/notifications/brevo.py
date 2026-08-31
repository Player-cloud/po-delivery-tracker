"""Brevo sender — production alternative to Resend (PRD §13).

Free tier: 300 emails/day. Needs `BREVO_API_KEY` and a verified sender.
"""

from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.services.notifications.base import EmailMessage, NotificationError, NotificationSender

settings = get_settings()

_API_URL = "https://api.brevo.com/v3/smtp/email"


class BrevoNotificationSender(NotificationSender):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.brevo_api_key
        if not self._api_key:
            raise NotificationError("BREVO_API_KEY is not set")

    def send(self, message: EmailMessage) -> None:
        payload: dict = {
            "sender": {"name": settings.smtp_from_name, "email": settings.smtp_from_address},
            "to": [{"email": message.to}],
            "subject": message.subject,
            "textContent": message.text_body,
        }
        if message.html_body:
            payload["htmlContent"] = message.html_body

        try:
            response = httpx.post(
                _API_URL,
                json=payload,
                headers={"api-key": self._api_key, "accept": "application/json"},
                timeout=15,
            )
        except httpx.HTTPError as exc:
            raise NotificationError(f"Brevo request failed: {exc}") from exc

        if response.status_code >= 400:
            raise NotificationError(
                f"Brevo rejected the message ({response.status_code}): {response.text}"
            )
