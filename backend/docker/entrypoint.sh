#!/bin/sh
# Shared entrypoint: apply migrations when the service owns some, then serve.
set -e

if [ -f /app/alembic.ini ]; then
  echo "==> [${SERVICE}] Running Alembic migrations..."
  alembic upgrade head
fi

echo "==> [${SERVICE}] Starting uvicorn on :8000"
exec uvicorn "${SERVICE}.main:app" --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips="*"
