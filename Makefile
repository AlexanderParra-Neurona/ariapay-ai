.PHONY: up down clean build logs dev ui scrape faq ingest-qdrant all

COMPOSE = docker compose --env-file .env -f docker-compose.yml

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

clean:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

dev:
	uv run uvicorn app.main:app --reload

ui:
	uv run python -m app.ui

scrape:
	uv run python scripts/scrape_pages.py

faq:
	uv run python scripts/generate_faq.py

ingest-qdrant:
	uv run python scripts/ingest_qdrant.py
