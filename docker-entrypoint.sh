#!/bin/sh
set -e

# Create runtime directories
mkdir -p /app/logs /app/static /app/media

# Ensure log files exist
touch /app/logs/errors.log
touch /app/logs/info.log

# Fix ownership
chown -R appuser:appuser /app/logs /app/static /app/media || true

# If gosu is available, drop privileges
if command -v gosu >/dev/null 2>&1; then
  # Wait for DB before celery
  if [ "$1" = "celery" ]; then
    python manage.py wait_for_tables || true
  fi

  exec gosu appuser "$@"
else
  if [ "$1" = "celery" ]; then
    python manage.py wait_for_tables || true
  fi

  exec "$@"
fi