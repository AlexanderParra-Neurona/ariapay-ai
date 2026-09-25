# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 2026-09-14

#### Added
- `/chat` now answers FAQ, account, and transaction questions through a single tool-calling agent built with LangGraph (`StateGraph` + `ToolNode`), instead of separate hardcoded doc/transaction/account branches.
- `search_faq` added as a callable tool alongside `get_account`/`search_transactions`, so the agent can choose which data source to query.

#### Changed
- Chat completions now go through `langchain-litellm`'s `ChatLiteLLM` (via a shared `get_chat_model()` factory) instead of a custom `LLMService.chat` method; `LLMService` is embeddings-only again. Classifiers and the agent now build on LangChain's message types and `.bind_tools()`/`.invoke()`.
- Tools (`search_faq`, `search_transactions`, `get_account`) are now LangChain `BaseTool`/`StructuredTool` instances instead of a custom `Tool` dataclass, so they plug directly into LangGraph's `ToolNode`.
- Chat model switched from `Meta-Llama-3.1-8B-Instruct-Turbo` to `Qwen/Qwen3-32B` for more reliable native tool-calling; Qwen3's "thinking" mode is disabled for chat completions to avoid burning the token budget on reasoning output.
- `get_tools()` now omits `get_account`/`search_transactions` entirely when the user has no access token, rather than exposing tools the model can't authenticate for.
- Account and transaction answer formatting deduplicated into a shared `app/services/formatting.py`, replacing copies in the router and individual tools.
- Dev server (`make dev`) now runs with `--no-sync` and reload scoped to `app/`, avoiding lockfile resync and restart loops from unrelated file changes.

### 2026-09-11

#### Added
- Function-calling tools for FAQ search, transaction search, and account lookup, each gated on the caller holding a signed-in access token.
- RAG quality eval harness (`ragas`): context precision/recall, faithfulness, answer relevancy/correctness, and semantic similarity, judged by a DeepInfra-backed LLM; runs only on demand via a dedicated `eval` pytest marker.

### 2026-09-10

#### Added
- Request/response tracing via custodia SDK: chat answering, classifiers, and hybrid/sparse retrieval and RRF fusion now emit spans, and FastAPI is instrumented end-to-end via OpenTelemetry.

#### Changed
- custodia-sdk moved from a vendored local package to a published PyPI dependency (previously pinned to a private git source).
- Langfuse tracing and its config/dependencies fully removed, replaced by custodia.

### 2026-09-02

#### Added
- Script for diagnosing and cleaning up Docker disk space.
- Railway deploy path as an alternative to the GCP VM: `railway.json`, env-sync script, and Docker build changes to work under Railway's builder.
- `APP_ENV` tag stamped on every LLM call, so dev/staging/prod traces are distinguishable in Langfuse dashboards.

#### Changed
- Self-hosted Langfuse stack (`docker-compose.langfuse.yml`, `.env.langfuse.example`) removed in favor of Langfuse Cloud.
- GCP deploy scripts moved under `deploy/gcp/`, separating them from generic VM/nginx setup to make room for other deploy targets.
- Nginx timeout settings increased on the chat endpoint to prevent connection cuts on longer responses.
- Minimal logging restored for auth failures, upstream API errors, and classifier parse fallback, since tracing only covered LLM calls and was otherwise silent.
- App now fails fast on a missing `QDRANT_API_KEY` instead of silently sending a placeholder value.

#### Fixed
- Staging domain corrected to `ariapay.id` across README/scripts; Docker enable step and nginx SSL block verification fixed on the deploy VM.
- Certbot's nginx setup now verifies the 443 block landed in the intended site file, preventing a stale default site from silently capturing it and 404ing requests.

#### Changed
- Docker image rebuilt as multi-stage (builder/runtime split) — production image no longer ships the `uv` toolchain or dev-only tooling, cutting image size ~57% (1.63GB → 723MB).
- Healthcheck now uses Python's `urllib` instead of `curl`, dropping the need to install `curl` in the runtime image.
- `fastembed`, `gradio`, `langchain-community`, and `requests` moved out of production dependencies into the dev group — `gradio`/`requests` are only used by the Gradio UI (not required for the API service), and `fastembed`/`langchain-community` were unused.

### 2026-09-01

#### Removed
- Redis and the FAQ cache layer removed (unused after cache path dropped) — `redis` dependency, service, config vars, and Docker Compose wiring all removed.

### 2026-08-31

#### Added
- `docs/API.md` API reference covering auth, chat, and health endpoints.
- Dedicated `qdrant-ingest` container runs document/transaction ingestion as part of `docker compose up`, instead of a manual script step.

#### Changed
- All API endpoints now live under a `/v1` prefix (e.g. `/chat` → `/v1/chat`, `/health` → `/v1/health`) — existing API consumers must update request paths.
- `app/main.py` split into per-resource routers (`app/routers/v1/{auth,chat,health}.py`) and request/response schemas (`app/schemas/`), replacing the single-file endpoint definitions.
- `LLMService.chat` metadata now passed through from query and transaction-scope classifiers, labeling their Langfuse traces individually.
- `docker/init_qdrant.sh` and `docker/pull_models.sh` (formerly under `scripts/`) relative paths updated in `docker-compose.yml`.

#### Removed
- Structured request/API-call logging (`app/logging_config.py`, `LOG_DIR`/`LOG_LEVEL` config) removed, along with all logger calls in the ariapay client, classifiers, and retrieval services.

### 2026-08-28

#### Added
- Langfuse tracing for chat/embedding calls, wired through LiteLLM's native callback (`LANGFUSE_ENABLED=true` + `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`/`LANGFUSE_HOST`).
- `docker-compose.langfuse.yml` for running a self-hosted Langfuse stack alongside the app.
- `LLMService.chat` now accepts optional `metadata` so call sites (query classifier, transaction scope classifier, doc answer) label their own Langfuse traces.

#### Changed
- Langfuse stack infra vars (db/queue/object-store creds, salt, init org/user) split out of `.env` into `.env.langfuse`; `LANGFUSE_ENABLED`/`PUBLIC_KEY`/`SECRET_KEY`/`HOST` stay in `.env` since the app reads those too. `make up`/`down`/`clean`/`build`/`logs` pass both via `--env-file`.
- Hardcoded literals in `docker-compose.langfuse.yml` (postgres/clickhouse/minio/redis creds, S3 bucket, salt, encryption key, nextauth secret) now read from env vars with matching defaults, instead of being baked into the compose file.

#### Fixed
- Pinned `langfuse<3` — litellm's langfuse integration reads `langfuse.version.__version__`, a module path removed in langfuse SDK v3+, causing every LLM call to error.
- Set `LANGFUSE_MIGRATION_V4_WRITE_MODE=dual` on `langfuse-web`/`langfuse-worker` — the v4 server defaults to `events_only` and rejects the legacy `trace-create`/`generation-create` events the pinned v2 SDK sends.

### 2026-08-27

#### Added
- Transaction queries now return full matching history (not just top-k) when user ask for "all" or category totals.

#### Changed
- Transaction search take scope param, route full-history vs limited results differently.
- Transaction Q&A now show concise summary plus itemized bullet list, instead of raw LLM-only answer.
- transaction spend summaries now computed by exact sum of matched transactions instead of LLM-generated text, giving deterministic totals.
- transaction queries now filter by classified spending category before summarizing.
- Chat/embedding calls now route through LiteLLM instead of provider-specific LangChain clients.
- Model config strings now include provider prefix (e.g. "ollama/...", "deepinfra/...").

#### Fixed
- Qdrant init container and app container now correctly read LLM_PROVIDER from shared `.llm-provider` file instead of relying on unset/inconsistent env var.
- no-match transaction queries now return proper "no transactions found" message instead of leaking None into answer.

### 2026-08-26

#### Added
- DeepInfra now selectable as LLM provider alongside Ollama, via `LLM_PROVIDER=deepinfra`.
- Chat response now include query category so client see how question classified.
- Bulk upsert support for document and transaction embeddings, reducing embedding API calls during ingestion.
- Ingestion now caches embeddings on disk, skipping re-embedding of unchanged content on repeat runs.

#### Changed
- env vars for chat/embed model split per-provider (`OLLAMA_*`, `DEEPINFRA_*`) instead of shared `CHAT_MODEL`/`EMBED_MODEL`/`EMBED_DIM` — deployments must update `.env`.
- Move embedding service module from qdrant package into llm package, no user-facing behavior change
- UI display category tag above answer text in chat response.
- Vector store embedding backend now injectable for custom embedding providers.
- `make up` now runs containers detached (background) instead of attached.

#### Fixed
- Privacy/security/data-handling questions now correctly answered as general FAQ instead of misclassified.

### 2026-08-24

#### Added
- Sparse retrieval exploration notebook: BM25 baseline, late-interaction reranking, and RAGAS-based quality evaluation.
- Pre-commit review hook now switches between Claude CLI or local Ollama model based on `.reviewer` config file, and drafts CHANGELOG.md entries from staged diffs.
- New LLM-based query classifier routes chat questions into general FAQ, transaction, or out-of-scope buckets.
- Out-of-scope questions now get canned decline reply instead of falling through to doc search.
- Seed data now include new merchant transaction dataset (`transactions.json`)
- Support transaction data alongside docs, enabling transaction-based search/queries.

#### Changed
- LLM backend is now pluggable via `LLM_PROVIDER` config instead of hardcoded to Ollama.
- Pre-commit hook wired into `.claude/settings.json` as PreToolUse hook on `git commit`, gated by new `.reviewer` file (set to `claude`).
- /chat account-data detection switch from keyword match to classifier-based routing.
- Ollama data now bind-mounts to a local `./ollama_data` folder on host instead of an internal Docker volume, for easier local access/backup.
- FAQ answers expand with more detail — fees change notice, refund policy, reseller/sublicense ban, data retention/deletion, account eligibility, termination/suspension rights, dispute jurisdiction, contact emails for legal/privacy
- Qdrant collection now use two named vectors (docs, transactions) instead of single unnamed vector; existing collections need migration.

#### Fixed
- Sparse (BM25) retriever now filter scroll to doc-type points only, avoiding transaction data polluting keyword search results.

### 2026-08-21

#### Changed
- Chat model is now configurable via `CHAT_MODEL` instead of hardcoded, used consistently by the FAQ generation script.
- Default Qdrant collection renamed from `faq` to `ariapay_docs` to reflect broader docs corpus, and made configurable end-to-end (compose services, init script).
- Qdrant ingestion now chunks markdown docs by heading instead of seeding from a flat FAQ JSON.

#### Removed
- `/chat` no longer short-circuits on a Qdrant FAQ match; it now always falls through to the no-answer response.

### 2026-08-20

#### Added
- Automatic Qdrant FAQ collection seeding on startup via a dedicated init service.

#### Changed
- Embedding model upgraded to `qwen3-embedding:8b` (from `nomic-embed-text`) for improved FAQ match quality.

### Added
- Chat API with FAQ answering and Ariapay account-question routing.
- Login flow with passcode verification.
- Gradio-based chat UI.
- FAQ generation script and `ariapay.id` page scraper for seed data.
- Structured request/API-call logging (rotating file + stream), configurable via `LOG_DIR`/`LOG_LEVEL`.
- Qdrant vector store service for FAQ similarity search.
- `/health` endpoint.

### Changed
- FAQ matching moved from Redis to Qdrant as the vector store, with a larger embedding model for improved match quality.
- FAQ matching switched from exact-text search to embedding-based similarity search (previously plain Redis text search).
- Ollama model pulls now run as a one-shot init step instead of gating app startup.

[unreleased]: https://github.com/AlexanderParra-Neurona/ariapay-ai/commits/main
