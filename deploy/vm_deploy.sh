#!/usr/bin/env bash
# Run ON the VM, from the repo root, after vm_bootstrap.sh and after `.env` is in place.
# Builds and (re)starts the app container on 127.0.0.1:${APP_PORT:-8000} — the VM's existing
# nginx (already fronting another backend) reverse-proxies the staging subdomain to it.
# Set APP_PORT in .env if 8000 is already taken by another service on this VM.
# See deploy/README.md for the nginx + certbot steps (one-time, separate from this script).
set -euo pipefail

if [ ! -f .env ]; then
  echo "Missing .env — copy .env.example to .env and fill in real staging secrets first." >&2
  exit 1
fi

docker compose --env-file .env -f docker-compose.yml up --build -d

app_port=$(grep -E '^APP_PORT=' .env | tail -1 | cut -d= -f2)
app_port=${app_port:-8000}

echo "Deployed. App listening on 127.0.0.1:${app_port}. Tail logs with:"
echo "  docker compose --env-file .env -f docker-compose.yml logs -f"
