#!/usr/bin/env bash
# Run locally, from the repo root, after `railway login` + `railway init`.
# Pushes every var in .env to the linked Railway service in one pass, then deploys once.
# Usage: bash deploy/railway/push_env.sh [path-to-env-file]
set -euo pipefail

ENV_FILE="${1:-.env}"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE — copy .env.example to .env and fill in real staging secrets first." >&2
  exit 1
fi

# APP_PORT only matters for local docker-compose's host port binding — Railway
# assigns/routes its own port via railway.json, so it's not pushed.
SKIP_KEYS=("APP_PORT")

echo "About to push every var in $ENV_FILE to Railway (including credentials like LOGIN_PASSWORD). Review $ENV_FILE now if unsure."
read -rp "Continue? [y/N] " confirm
[ "$confirm" = "y" ] || [ "$confirm" = "Y" ] || { echo "Aborted."; exit 1; }

while IFS='=' read -r key value; do
  [ -z "$key" ] && continue
  case "$key" in
    \#*) continue ;;
  esac
  skip=false
  for sk in "${SKIP_KEYS[@]}"; do
    [ "$key" = "$sk" ] && skip=true && break
  done
  [ "$skip" = true ] && continue

  echo "Setting $key"
  railway variable set "$key=$value" --skip-deploys
done < "$ENV_FILE"

echo
echo "All variables set. Deploying..."
railway up
