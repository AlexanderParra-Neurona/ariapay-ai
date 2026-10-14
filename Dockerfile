FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv==0.9.7

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
RUN uv sync --frozen --no-dev


FROM python:3.11-slim AS runtime

WORKDIR /app

RUN groupadd --gid 1000 app && useradd --uid 1000 --gid app --no-create-home app

COPY --from=builder --chown=app:app /app/.venv ./.venv
COPY --from=builder --chown=app:app /app/app ./app
COPY --chown=app:app .llm-provider ./.llm-provider

ARG APP_PORT=8000
ENV APP_PORT=${APP_PORT}
ENV PATH="/app/.venv/bin:$PATH"
USER app

EXPOSE ${APP_PORT}

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${APP_PORT}/v1/health')" || exit 1

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT}"]
