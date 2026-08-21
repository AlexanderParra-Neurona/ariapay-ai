.PHONY: up down clean build logs dev redis ui seed seed-clear scrape faq all setup-hooks

setup-hooks:
	@git config core.hooksPath .githooks

up:
	docker compose up --build

down:
	docker compose down

clean:
	docker compose down -v

build:
	docker compose build

logs:
	docker compose logs -f

all:
	$(MAKE) -j3 redis dev ui

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
