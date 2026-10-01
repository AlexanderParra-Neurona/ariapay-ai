# ariabot

Minimal FastAPI + LangGraph agent service with Redis-backed semantic FAQ cache.

Requires [Ollama](https://ollama.com) running locally with `nomic-embed-text` pulled (`ollama pull nomic-embed-text`).

## Run

```bash
cp .env.example .env
docker compose up --build
make seed   # populate dummy FAQ data
```

App at `http://localhost:8000`. Endpoints: `GET /v1/health`, `POST /v1/chat` (`{"question": "..."}`).

Redis GUI (redis-commander) at `http://localhost:8081`.

## Local dev (no docker)

```bash
uv sync
make redis  # redis-stack-server, needed for vector search
uv run uvicorn app.main:app --reload
make seed
```

## Custodia tracing

Uses [`custodia-sdk`](https://pypi.org/project/custodia-sdk/) to export OpenTelemetry traces (HTTP requests, agent loop, tool calls, retrieval, LLM calls) to a Custodia ingest endpoint. Set in `.env`:

```bash
CUSTODIA_INGEST_URL=http://localhost:8000/v1/traces   # http://host.docker.internal:8000/v1/traces under docker compose
CUSTODIA_API_KEY=...
CUSTODIA_SERVICE_NAME=ariabot
```

## How the cache works

FAQ questions are embedded (`nomic-embed-text`, 768-dim) and stored in a Redis vector index (`redis-stack`, HNSW/COSINE). Incoming questions are embedded and matched via KNN; a hit above `FAQ_MATCH_THRESHOLD` (default `0.85`) short-circuits generation. No exact-text match required — paraphrased questions still hit.
