FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create runtime dirs and a non-root user
RUN mkdir -p /app/logs /app/static /app/media \
    && useradd --create-home appuser || true \
    && chown -R appuser:appuser /app/logs /app/static /app/media /app

# Install gosu for simple privilege dropping at container start
RUN set -eux; \
    apt-get update && apt-get install -y --no-install-recommends ca-certificates wget gnupg dirmngr && \
    GOSU_VERSION=1.14 && \
    dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')" && \
    wget -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-${dpkgArch}" && \
    chmod +x /usr/local/bin/gosu || true

# Copy and set entrypoint
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
