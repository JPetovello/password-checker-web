FROM python:3.13-alpine

WORKDIR /app

# Accept version build argument and set it as an environment variable
ARG VERSION=latest
ENV APP_VERSION=$VERSION

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
