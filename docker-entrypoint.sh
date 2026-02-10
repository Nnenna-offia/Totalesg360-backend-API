#!/bin/sh
set -e

# Create runtime directories and ensure ownership
mkdir -p /app/logs /app/static /app/media
chown -R appuser:appuser /app/logs /app/static /app/media || true

# If gosu is available, use it to drop privileges to `appuser` for the commanded process.
if command -v gosu >/dev/null 2>&1; then
  exec gosu appuser "$@"
else
  exec "$@"
fi
