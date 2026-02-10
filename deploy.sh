#!/usr/bin/env bash
set -e

ENV=${1:-dev}
COMPOSE_FILES="docker-compose.yml:docker-compose.$ENV.yml"

# Build docker compose args
DOCKER_COMPOSE_ARGS=""
for f in ${COMPOSE_FILES//:/ }; do
  DOCKER_COMPOSE_ARGS+=" -f $f"
done

# Pull/build and start
docker compose $DOCKER_COMPOSE_ARGS pull || true
docker compose $DOCKER_COMPOSE_ARGS up -d --build

sleep 5

# Run migrations and collectstatic on web
if docker compose $DOCKER_COMPOSE_ARGS ps -q web >/dev/null 2>&1; then
  docker compose $DOCKER_COMPOSE_ARGS exec -T web python manage.py migrate --noinput || true
  docker compose $DOCKER_COMPOSE_ARGS exec -T web python manage.py collectstatic --noinput || true
fi

# Restart workers if present
for svc in worker celery celery_worker beat celery-beat; do
  if docker compose $DOCKER_COMPOSE_ARGS ps -q $svc >/dev/null 2>&1; then
    docker compose $DOCKER_COMPOSE_ARGS restart $svc || true
  fi
done

# Tail logs for quick feedback
docker compose $DOCKER_COMPOSE_ARGS logs --tail=100 --no-color || true
