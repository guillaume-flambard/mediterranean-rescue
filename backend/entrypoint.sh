#!/bin/sh
# Entry point of the production image. `serve` migrates, then starts gunicorn; any other
# command is a manage.py command (sync_logbook --every 21600, sync_sheets --every 300, …).
set -eu
manage() { uv run --no-sync python backend/manage.py "$@"; }

if [ "${1:-serve}" = "serve" ]; then
  manage migrate --noinput
  exec uv run --no-sync gunicorn --chdir backend rescue.wsgi:application \
    --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-2}" --threads 1 --timeout 30 \
    --access-logfile -
fi
exec uv run --no-sync python -u backend/manage.py "$@"
