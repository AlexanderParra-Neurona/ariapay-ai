FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

RUN groupadd --gid 1000 app && useradd --uid 1000 --gid app --no-create-home app

COPY --chown=app:app pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY --chown=app:app app ./app
COPY --chown=app:app scripts ./scripts

ENV UV_CACHE_DIR=/app/.cache/uv
USER app

EXPOSE 8000

CMD ["uv", "run", "--frozen", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
