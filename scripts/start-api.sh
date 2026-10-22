#!/usr/bin/env bash
# Production entrypoint for the API container.
#   1. Applies pending database migrations (idempotent).
#   2. Optionally runs the Celery worker in the same container (RUN_EMBEDDED_WORKER=true), for
#      single-service deployments where a separate worker is not available.
#   3. Starts uvicorn on $PORT (platforms such as Render/Railway inject it).
set -euo pipefail

echo "[start] applying database migrations"
alembic upgrade head

if [ "${RUN_EMBEDDED_WORKER:-false}" = "true" ]; then
  echo "[start] launching embedded celery worker"
  celery -A app.workers.celery_app worker --loglevel=info --pool=solo &
fi

echo "[start] launching api on port ${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --no-server-header
