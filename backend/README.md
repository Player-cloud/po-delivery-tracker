# Backend — Setup

## 1. Start Postgres and Mailhog

From the repo root:

```bash
docker compose up -d db mailhog
```

- Postgres: `localhost:5432` (user `postgres`, password `postgres`, db `po_tracking`)
- Mailhog web UI (view "sent" emails during dev): http://localhost:8025

## 2. Set up the Python environment

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## 3. Run the migration

```bash
alembic upgrade head
```

This creates all five tables (`users`, `po_lines`, `attachments`, `notification_history`,
`configuration`) and seeds the default reminder thresholds.

Verify it worked:

```bash
docker exec -it $(docker compose ps -q db) psql -U postgres -d po_tracking -c "\dt"
```

You should see all five tables listed.

## 4. Important: validate the hand-authored migration

`0001_initial_schema.py` was written by hand (there's no live database available in the
environment it was authored in). Before trusting it:

```bash
alembic upgrade head
alembic revision --autogenerate -m "check for drift"
```

Open the newly generated revision file. If its `upgrade()`/`downgrade()` bodies are empty
(just `pass`), the schema matches the models exactly and you can delete that empty
check-in revision. If it contains real operations, that's a mismatch between
`0001_initial_schema.py` and the models — fix `0001` directly (it hasn't shipped anywhere
yet, so it's safe to edit in place) rather than layering a second migration on top.

## 5. Reminder emails (M1)

The daily reminder pass lives in `app/services/reminders.py`. It is not scheduled
in-process — an external caller triggers it once a day.

**Run it manually (dev):** start Mailhog (`docker compose up -d mailhog`), then:

```bash
python -m scripts.run_reminders
```

Sent reminders show up at http://localhost:8025.

**Via the HTTP endpoint** (what the production scheduler calls):

```bash
curl -X POST http://localhost:8000/api/v1/internal/run-reminders \
  -H "Authorization: Bearer $CRON_SECRET"
```

`CRON_SECRET`, `FRONTEND_BASE_URL`, `EMAIL_BACKEND` (`smtp` | `resend` | `brevo`)
and the other reminder settings are in `.env.example`. In production a GitHub
Actions workflow (`.github/workflows/reminders.yml`) makes this call daily.

## 6. Checks (M5)

The same checks CI runs (`.github/workflows/ci.yml`):

```bash
ruff check .            # lint
ruff format --check .   # formatting (drop --check to apply)
pytest                  # 83 tests, SQLite-backed, no services needed
```

Config lives in `pyproject.toml`. A separate CI job runs `alembic upgrade head`
then `alembic downgrade base` against a real Postgres to catch migration drift.

## 7. Attachments (M3)

Files attach per PO line via `/api/v1/po-lines/{id}/attachments` (upload / list /
download / delete). Bytes live behind `app/services/storage/`:

- `STORAGE_BACKEND=local` (default) — files under `LOCAL_UPLOAD_DIR` (`./uploads`)
- `STORAGE_BACKEND=s3` — S3-compatible; set `S3_BUCKET`, `S3_ENDPOINT_URL`,
  `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` (Cloudflare R2 in production).
  Needs `boto3` (in `requirements.txt`, imported lazily).

Upload limits: `ATTACHMENT_MAX_BYTES` (10 MB) and `ATTACHMENT_ALLOWED_EXTENSIONS`.

## 8. Next

M6 — production deployment (Vercel + Render + Neon + R2).
