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

## Docura (FAQ and product docs)

The `search_faq` tool answers general questions by calling [Docura](../docura)'s
`POST /v1/query` (`app/services/docura_service.py`). Set in `.env`:

```bash
DOCURA_API_URL=http://localhost:8001   # Docura API base, no /v1
DOCURA_API_KEY=...                     # same value as API_KEY on the Docura API
```

- In the workspace stack (`neurona/docker-compose.yml`) ariabot reaches Docura at
  `http://docura-api:8001` over the compose network; only `DOCURA_API_KEY` is read
  from `.env`.
- On Railway, use Docura's public URL (`https://docura-api-....up.railway.app`) and the
  `API_KEY` from `docura/deploy/railway/.env`.
- A Docura query makes two LLM calls, so the client waits up to 120s. Timeouts,
  connection errors, 401s and 5xx all fall back to "Sorry, I don't have information on
  that." and are logged as `Docura query: ...`; a 401 means the keys don't match.

## Langfuse tracing (optional)

Uses the [Langfuse Python SDK](https://langfuse.com/docs/sdk/python/sdk-v3) (v4) to trace HTTP requests, the agent loop, tool calls, retrieval, and LLM calls. Sign up, create a project, and set in `.env`:

```bash
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com   # or https://jp.cloud.langfuse.com / https://us.cloud.langfuse.com for a regional deployment
```

Credentials and PII (passwords, passcodes, tokens, email, phone numbers) are redacted by `app.tracing.mask_pii` before spans leave the process. Use the `app.tracing` decorators rather than a bare `@observe` so arguments are recorded by name and the mask can see them.

## How the cache works

FAQ questions are embedded (`nomic-embed-text`, 768-dim) and stored in a Redis vector index (`redis-stack`, HNSW/COSINE). Incoming questions are embedded and matched via KNN; a hit above `FAQ_MATCH_THRESHOLD` (default `0.85`) short-circuits generation. No exact-text match required — paraphrased questions still hit.
