.PHONY: up down clean build logs dev redis ui seed seed-clear all

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

dev:
	uv run uvicorn app.main:app --reload

ui:
	uv run python -m app.ui

seed:
	uv run python scripts/seed_redis.py

seed-clear:
	uv run python scripts/seed_redis.py --clear
