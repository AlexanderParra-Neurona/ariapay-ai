.PHONY: up down clean build logs dev ui scrape faq ingest-qdrant all

COMPOSE = docker compose --env-file .env -f docker-compose.yml
APP_PORT ?= $(or $(shell grep -E '^APP_PORT=' .env 2>/dev/null | tail -1 | cut -d= -f2),8000)

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

clean:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

dev:
	uv run --no-sync uvicorn app.main:app --reload --reload-dir app --port $(APP_PORT)

ui:
	uv run python -m app.ui

scrape:
	uv run python scripts/scrape_pages.py

faq:
	uv run python scripts/generate_faq.py

ingest-qdrant:
	uv run python scripts/ingest_qdrant.py
