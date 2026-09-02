#!/usr/bin/env bash
# Run ON the VM, from the repo root. Removes ariabot's containers + nginx site only.
# Never touches the existing backend's containers, nginx site, or certs.
set -euo pipefail

STAGING_DOMAIN="${1:-}"

echo "== Stopping ariabot containers =="
if [ -f .env ]; then
  docker compose --env-file .env -f docker-compose.yml down
else
  echo ".env not found, skip (containers likely already down)."
fi

echo "== Removing ariabot nginx site =="
if [ -L /etc/nginx/sites-enabled/ariabot ] || [ -f /etc/nginx/sites-enabled/ariabot ]; then
  sudo rm /etc/nginx/sites-enabled/ariabot
  echo "Removed sites-enabled/ariabot."
else
  echo "sites-enabled/ariabot not present, skip."
fi

if [ -f /etc/nginx/sites-available/ariabot ]; then
  sudo rm /etc/nginx/sites-available/ariabot
  echo "Removed sites-available/ariabot."
else
  echo "sites-available/ariabot not present, skip."
fi

echo "== Validating nginx config before reload =="
sudo nginx -t

echo "== Reloading nginx =="
echo "systemctl reload nginx" | sudo sh

if [ -n "$STAGING_DOMAIN" ]; then
  echo "== Removing certbot cert for $STAGING_DOMAIN (optional, safe to leave) =="
  sudo certbot delete --cert-name "$STAGING_DOMAIN" --non-interactive || \
    echo "certbot delete skipped/failed (cert may not exist) — not fatal."
else
  echo "No domain passed — skipping certbot cert cleanup. Run with:"
  echo "  bash deploy/vm_teardown.sh staging-ai.ariapay.id"
  echo "to also remove the cert."
fi

echo
echo "Done. ariabot containers stopped, its nginx site removed, nginx reloaded."
echo "Existing backend's containers/nginx site were not touched."
echo
echo "Remaining manual cleanup (if desired):"
echo "  - Delete the DNS A record in Cloud DNS for the staging subdomain."
echo "  - cd .. && rm -rf $(basename "$(pwd)")   # deletes the cloned repo directory"
