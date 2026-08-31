# Python 3.13, not 3.14 — deliberately older than local dev. This is a fresh
# Linux environment built from scratch, so it doesn't need to match your
# Windows machine's Python version, and 3.13 has mature, stable wheel support
# for every package here (sidesteps the exact pain we hit locally with 3.14).
FROM python:3.13-slim

# Prevents Python from writing .pyc files and buffers output immediately
# (so `docker logs` shows things in real time instead of batched).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy just requirements.txt first, install, THEN copy the rest of the code.
# This is a deliberate ordering trick: Docker caches each step, and only
# re-runs a step (and everything after it) if its inputs changed. Since
# requirements.txt changes far less often than your actual code, this means
# `docker build` skips the slow `pip install` step entirely on most rebuilds
# — it only re-runs when requirements.txt itself changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy everything else (app code, alembic, scripts).
COPY . .

EXPOSE 8000

# In production you'd drop --reload (it's a dev convenience that watches
# for file changes) — for now, matches what you've been running locally.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]