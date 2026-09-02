.PHONY: up down clean build logs dev redis ui seed seed-clear scrape faq ingest-qdrant all setup-hooks

setup-hooks:
	@git config core.hooksPath .githooks

LLM_PROVIDER := $(shell tr -d '[:space:]' < .llm-provider 2>/dev/null)

COMPOSE = docker compose --env-file .env -f docker-compose.yml
ifeq ($(LLM_PROVIDER),ollama)
COMPOSE += --profile ollama
endif

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

clean:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

redis:
	docker run --rm -p 6379:6379 --name ariabot-redis redis/redis-stack-server:latest

dev: setup-hooks
	uv run uvicorn app.main:app --reload

ui: setup-hooks
	uv run python -m app.ui

seed:
	uv run python scripts/seed_redis.py

seed-clear:
	uv run python scripts/seed_redis.py --clear

scrape:
	uv run python scripts/scrape_pages.py

faq:
	uv run python scripts/generate_faq.py

ingest-qdrant:
	uv run python scripts/ingest_qdrant.py
