# ariabot

FastAPI + LangGraph tool-calling agent for Ariapay. It answers FAQ questions via
Docura and, for signed-in users, account and transaction questions via the Ariapay
API. See [`docs/API.md`](docs/API.md) for the HTTP API.

## Run

```bash
cp .env.example .env   # fill in DEEPINFRA_*, ARIAPAY_*, DOCURA_*, LANGFUSE_*
make up                # docker compose up --build -d
```

App at `http://localhost:8000` (`APP_PORT`). Endpoints: `GET /v1/health`,
`POST /v1/auth/login`, `POST /v1/chat`.

## Local dev (no docker)

```bash
uv sync
make dev   # uvicorn with reload on app/
```

## Ariapay API

Two base URLs, both without a trailing `/api/v1`:

```bash
ARIAPAY_API_URL=...           # auth and account (login, passcode, profile)
ARIAPAY_PAYMENT_API_URL=...   # payment service, e.g. https://api.ariapay.id/payment
```

`list_transactions` and `get_spending_summary` read transactions, categories, and
expenses from `ARIAPAY_PAYMENT_API_URL` (`app/services/ariapay_transactions_service.py`).
That client only sends GET requests; anything else raises `AriapayReadOnlyViolation`.

A plain-text `404 page not found` means the base URL or path is wrong and is reported
to the user as a fetch failure. Only a JSON 404 with an `err_code` is treated as "not
found" (e.g. an unknown category).

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

The masked client is created when `app.tracing` is imported. Langfuse keeps the first client built per public key, so any module that calls `get_client()` or builds a `CallbackHandler` at import time must import `app.tracing` first, or its spans go out unmasked (`tests/test_tracing.py` checks this).
