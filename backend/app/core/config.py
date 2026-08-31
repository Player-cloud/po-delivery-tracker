"""
Centralized application configuration.

All environment-specific values (DB connection, secrets, storage backend, etc.)
are read here and nowhere else, so switching from local dev to Azure later is a
config change, not a code change.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- App ---
    app_name: str = "PO Delivery Tracking System"
    environment: str = "development"  # development | production
    debug: bool = True

    # --- Database ---
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/po_tracking"

    # --- Auth ---
    secret_key: str = "change-me-in-.env"  # noqa: S105 (dev default only)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- File storage ---
    storage_backend: str = "local"  # local | azure_blob
    local_upload_dir: str = "./uploads"
    azure_storage_connection_string: str | None = None
    azure_storage_container: str = "attachments"

    # --- Email ---
    email_backend: str = "smtp"  # smtp | resend | brevo
    smtp_host: str = "localhost"
    smtp_port: int = 1025  # Mailhog default
    smtp_from_address: str = "po-tracking@example.com"
    smtp_from_name: str = "PO Delivery Tracker"
    # Only needed when email_backend is the matching provider (production).
    resend_api_key: str | None = None
    brevo_api_key: str | None = None

    # --- Reminders (M1) ---
    # Fallback thresholds if the CONFIGURATION table has no row — the DB value
    # (seeded by migration 0001/0003, editable via PUT /config/thresholds) wins.
    default_reminder_thresholds_days: list[int] = [30, 60, 90]
    # Shared secret the daily scheduler must present as `Authorization: Bearer <...>`
    # to call POST /internal/run-reminders. Override in every real environment.
    cron_secret: str = "dev-cron-secret-change-me"  # noqa: S105 (dev default only)
    # Base URL of the frontend, used to build the "open this PO line" link in emails.
    frontend_base_url: str = "http://localhost:3000"
    # Safety-net recipient for a line that still has no active assignee despite
    # Assigned To being required (PRD §14 Q2). None means "log and skip, retry".
    reminder_fallback_email: str | None = None
    # Overdue escalation (PRD §14 Q3): the assignee gets the daily overdue
    # reminder for this many days; after that it goes to REMINDER_ESCALATION_EMAIL.
    reminder_overdue_escalation_days: int = 7
    reminder_escalation_email: str | None = None
    # Guardrails for a single run (PRD §10): stop the pass from exceeding the
    # backend host's request timeout or the email provider's free-tier daily cap.
    reminder_batch_size: int = 500
    reminder_max_emails_per_run: int = 90


@lru_cache
def get_settings() -> Settings:
    """Cached so Settings() is only parsed once per process."""
    return Settings()
