# --- Stage 1: Builder ---
FROM python:3.13-alpine AS builder

WORKDIR /app

# Install build dependencies required for compiling C-extensions on Alpine
RUN apk add --no-cache gcc g++ musl-dev libffi-dev python3-dev build-base

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Final Runner ---
FROM python:3.13-alpine

WORKDIR /app

# Accept version and source build arguments
ARG VERSION=latest
ENV APP_VERSION=$VERSION

ARG SOURCE=docker_standalone
ENV APP_SOURCE=$SOURCE

# Align Unraid 'nobody:users' (99:100) permissions
RUN getent group 100 || addgroup -g 100 users && \
    adduser -D -u 99 -G users nobody 2>/dev/null || true

# Copy compiled Python packages from the builder stage
COPY --from=builder /install /usr/local

COPY . .

# Assign ownership of the app directory to nobody:users
RUN chown -R 99:100 /app

# Switch execution context away from root to non-root UID 99
USER 99:100

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
