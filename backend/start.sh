#!/usr/bin/env sh
# Container entrypoint: apply migrations, then serve.
# `alembic upgrade head` is a no-op when the DB is already at head, so it's safe
# to run on every start / restart. If it fails the container exits and the
# deploy is marked failed — which is what we want (don't serve a bad schema).
set -e

alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
