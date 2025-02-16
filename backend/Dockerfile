# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.3
FROM python:${PYTHON_VERSION}-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a writable cache directory before creating the user
ENV TRANSFORMERS_CACHE=/tmp/huggingface

# Create a non-privileged user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/app" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Ensure the cache directory is writable
RUN mkdir -p ${TRANSFORMERS_CACHE} && chmod -R 777 ${TRANSFORMERS_CACHE}

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install --no-cache-dir -r requirements.txt

# Switch to the non-privileged user
USER appuser

# Copy source code
COPY . .

# Expose the application port
EXPOSE 8000

# Run the application
CMD uvicorn 'main:app' --host=0.0.0.0 --port=8000