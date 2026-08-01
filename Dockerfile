FROM python:3.13-alpine

WORKDIR /app

# Accept version and source build arguments and set them as environment variables
ARG VERSION=latest
ENV APP_VERSION=$VERSION

ARG SOURCE=docker_standalone
ENV APP_SOURCE=$SOURCE

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
