# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_CACHE_DIR=/tmp/.uv-cache \
    UV_HTTP_TIMEOUT=120

# Native uv binary.
COPY --from=ghcr.io/astral-sh/uv:0.5.9 /uv /uvx /bin/

WORKDIR /workspace

COPY requirements.txt /tmp/requirements.txt

# Persist uv download/wheel cache across builds.
RUN --mount=type=cache,target=/tmp/.uv-cache \
    uv pip install --system -r /tmp/requirements.txt

COPY . /workspace

CMD ["sleep", "infinity"]