FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    JARVISNT_BASE_DIR=/runpod-volume/jarvisnt \
    JARVISNT_DEVICE_TYPE=auto

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.11.26 /uv /uvx /usr/local/bin/
COPY pyproject.toml uv.lock README.md ./
COPY jarvisnt ./jarvisnt
COPY scripts ./scripts
COPY runpod_worker ./runpod_worker

RUN uv sync --frozen --extra gpu --no-dev

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "runpod_worker.handler"]
