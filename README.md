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

## Langfuse tracing (optional)

Set `LANGFUSE_ENABLED=true` and `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` in `.env` to trace chat/embedding calls. Infra-only vars (db creds, salt, init org/user) live in `.env.langfuse` — copy `.env.langfuse.example` to get started. To self-host Langfuse:

```bash
cp .env.langfuse.example .env.langfuse
make up   # or: docker compose --env-file .env --env-file .env.langfuse -f docker-compose.yml -f docker/docker-compose.langfuse.yml up --build -d
```

Org/project/user/API keys are auto-provisioned on first boot from `.env.langfuse`'s `LANGFUSE_INIT_*` vars plus `.env`'s `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` — no manual signup. Log into `http://localhost:3000` with `LANGFUSE_INIT_USER_EMAIL`/`LANGFUSE_INIT_USER_PASSWORD`.

## How the cache works

FAQ questions are embedded (`nomic-embed-text`, 768-dim) and stored in a Redis vector index (`redis-stack`, HNSW/COSINE). Incoming questions are embedded and matched via KNN; a hit above `FAQ_MATCH_THRESHOLD` (default `0.85`) short-circuits generation. No exact-text match required — paraphrased questions still hit.
