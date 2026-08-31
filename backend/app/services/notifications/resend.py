"""Resend sender — the production default (PRD §13).

Free tier: 3,000 emails/month (~100/day). Needs `RESEND_API_KEY` and a verified
sender domain for `SMTP_FROM_ADDRESS`.
"""

from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.services.notifications.base import EmailMessage, NotificationError, NotificationSender

settings = get_settings()

_API_URL = "https://api.resend.com/emails"


class ResendNotificationSender(NotificationSender):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.resend_api_key
        if not self._api_key:
            raise NotificationError("RESEND_API_KEY is not set")

    def send(self, message: EmailMessage) -> None:
        payload: dict = {
            "from": f"{settings.smtp_from_name} <{settings.smtp_from_address}>",
            "to": [message.to],
            "subject": message.subject,
            "text": message.text_body,
        }
        if message.html_body:
            payload["html"] = message.html_body

        try:
            response = httpx.post(
                _API_URL,
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=15,
            )
        except httpx.HTTPError as exc:
            raise NotificationError(f"Resend request failed: {exc}") from exc

        if response.status_code >= 400:
            raise NotificationError(
                f"Resend rejected the message ({response.status_code}): {response.text}"
            )
