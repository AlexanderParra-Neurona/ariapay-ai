# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
