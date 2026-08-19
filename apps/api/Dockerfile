FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if required for compiling C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy package config and install dependencies
COPY apps/api/pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy application code and migrations
COPY apps/api/chirp_api ./chirp_api
COPY apps/api/alembic ./alembic
COPY apps/api/alembic.ini ./

ENV PYTHONUNBUFFERED=1
ENV GRPC_PORT=50051
ENV HTTP_PORT=3001

EXPOSE 50051 3001

CMD ["python", "-m", "chirp_api.main"]
