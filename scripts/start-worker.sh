#!/usr/bin/env bash
# Production entrypoint for the Celery ingestion worker.
set -euo pipefail
exec celery -A app.workers.celery_app worker --loglevel=info --pool=solo
