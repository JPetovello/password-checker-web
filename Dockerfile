FROM python:3.13-alpine

WORKDIR /app

# Accept version and source build arguments and set them as environment variables
ARG VERSION=latest
ENV APP_VERSION=$VERSION

ARG SOURCE=docker_standalone
ENV APP_SOURCE=$SOURCE

# Upgrade pip/setuptools/wheel and align Unraid 'nobody:users' (99:100)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    getent group 100 || addgroup -g 100 users && \
    adduser -D -u 99 -G users nobody 2>/dev/null || true

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Assign ownership of the app directory to nobody:users
RUN chown -R 99:100 /app

# Switch execution context away from root to non-root UID 99
USER 99:100

EXPOSE 5000

CMD ["python", "app.py"]
