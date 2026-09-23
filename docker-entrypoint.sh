#!/bin/sh
set -e

echo "[entrypoint] Running database migrations..."
alembic upgrade head || echo "[entrypoint] WARNING: alembic upgrade failed or DATABASE_URL not reachable yet; the app will still try to create tables on startup."

if [ "$#" -eq 0 ]; then
  echo "[entrypoint] No command given, starting web server on port ${PORT:-8000}..."
  exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
else
  echo "[entrypoint] Starting: $*"
  exec "$@"
fi
