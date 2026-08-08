# --- Builder Stage ---
FROM python:3.13-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir wheel && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# --- Final Stage ---
FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY . .

# Ensure data directory exists and assign permissions to nobody:users (99:100)
RUN mkdir -p /app/data && \
    groupadd -g 100 users || true && \
    useradd -u 99 -g users -m -s /bin/bash nobody || true && \
    chown -R 99:100 /app

ARG APP_VERSION=latest
ENV APP_VERSION=${APP_VERSION}

ENV HOME=/tmp

# Native Docker Healthcheck using Python built-in urllib
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/healthz')" || exit 1

USER 99:100

ENV PORT=5000 \
    PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
