#!/usr/bin/env bash
# Run ON the VM once, from the repo root, after vm_deploy.sh.
# Adds the nginx site for this app's staging subdomain and issues its Let's Encrypt cert.
# Fill in the 2 values below (or pass as env vars), then: bash deploy/vm_nginx_setup.sh
set -euo pipefail

STAGING_DOMAIN="${STAGING_DOMAIN:-staging-ai.ariapay.com}"
APP_PORT="${APP_PORT:-8000}"   # must match APP_PORT in .env

SITE_FILE="/etc/nginx/sites-available/ariabot"

if [ -e "$SITE_FILE" ]; then
  echo "$SITE_FILE already exists, skip nginx site creation."
else
  sudo cp deploy/ariabot.nginx.conf "$SITE_FILE"
  sudo sed -i "s/STAGING_DOMAIN_PLACEHOLDER/$STAGING_DOMAIN/" "$SITE_FILE"
  sudo sed -i "s/APP_PORT_PLACEHOLDER/$APP_PORT/" "$SITE_FILE"
  echo "Wrote $SITE_FILE for $STAGING_DOMAIN -> 127.0.0.1:$APP_PORT"
fi

if [ -e "/etc/nginx/sites-enabled/ariabot" ]; then
  echo "Site already enabled, skip symlink."
else
  sudo ln -s "$SITE_FILE" /etc/nginx/sites-enabled/ariabot
  echo "Enabled site."
fi

sudo nginx -t
echo "systemctl reload nginx" | sudo sh

# Requires DNS to already resolve to this VM (see deploy/gcp_setup.sh / README step 1).
sudo certbot --nginx -d "$STAGING_DOMAIN"

echo
echo "Done. Confirm the existing backend's site is untouched:"
echo "  sudo nginx -t"
echo "  ls /etc/nginx/sites-enabled/"
