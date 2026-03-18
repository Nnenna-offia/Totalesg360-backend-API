#!/bin/sh
set -e

# Create runtime directories and ensure ownership
mkdir -p /app/logs /app/static /app/media
chown -R appuser:appuser /app/logs /app/static /app/media || true

# If gosu is available, use it to drop privileges to `appuser` for the commanded process.
if command -v gosu >/dev/null 2>&1; then
  # If starting Celery worker or beat, wait for DB tables first to avoid ProgrammingError
  if [ "$1" = "celery" ] || [ "$1" = "celery" ] && [ "$2" != "--help" ]; then
    # call manage.py wait_for_tables with dashboard defaults before running celery
    python manage.py wait_for_tables || true
  fi
  exec gosu appuser "$@"
else
  if [ "$1" = "celery" ] || [ "$1" = "celery" ] && [ "$2" != "--help" ]; then
    python manage.py wait_for_tables || true
  fi
  exec "$@"
fi
