"""
Run the daily reminder pass once, from the command line.

Use this in local dev (watch the results land in Mailhog at http://localhost:8025)
or as the thing a plain cron entry calls on a self-hosted box. Production uses the
HTTP endpoint instead (POST /api/v1/internal/run-reminders via GitHub Actions).

Usage (from backend/, venv active, .env configured, DB up):
    python -m scripts.run_reminders
"""
import logging

from app.db.session import SessionLocal
from app.services.reminders import run_reminders


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    db = SessionLocal()
    try:
        result = run_reminders(db)
    finally:
        db.close()

    print(
        f"\nthresholds={result.thresholds_days}\n"
        f"scanned={result.lines_scanned}  sent={result.emails_sent}  "
        f"escalated={result.emails_escalated}  "
        f"already_sent={result.skipped_already_sent}  "
        f"no_recipient={result.skipped_no_recipient}  errors={result.errors}  "
        f"capped={result.capped}"
    )
    for line in result.details:
        print(f"  - {line}")


if __name__ == "__main__":
    main()
