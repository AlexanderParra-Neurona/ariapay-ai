#!/usr/bin/env bash
# Run ON the VM once, from the repo root, after vm_deploy.sh.
# Adds the nginx site for this app's staging subdomain and issues its Let's Encrypt cert.
# Fill in the 2 values below (or pass as env vars), then: bash deploy/vm_nginx_setup.sh
set -euo pipefail

STAGING_DOMAIN="${STAGING_DOMAIN:-staging-ai.ariapay.id}"
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

# Certbot's nginx plugin edits whichever server block it finds matching server_name
# across ALL enabled sites — if another site (e.g. sites-enabled/default) already had
# or picked up a matching server_name, it can write the SSL block there instead of here,
# leaving this file with no 443 block and requests silently 404-ing. Verify it landed
# in the right file before declaring success.
if sudo grep -q "listen 443" "$SITE_FILE"; then
  echo "Confirmed: 443 block added to $SITE_FILE."
else
  echo
  echo "WARNING: $SITE_FILE has no 'listen 443' block after certbot ran." >&2
  echo "Certbot likely wrote the SSL block into a different site (check sites-enabled/default" >&2
  echo "and any other file matching 'server_name $STAGING_DOMAIN'):" >&2
  echo "  sudo grep -rl \"$STAGING_DOMAIN\" /etc/nginx/sites-enabled/" >&2
  echo "Move the 443 server block (with its ssl_certificate lines) into $SITE_FILE," >&2
  echo "add the proxy_pass location block, then: sudo nginx -t && sudo systemctl reload nginx" >&2
fi

echo
echo "Done. Confirm the existing backend's site is untouched:"
echo "  sudo nginx -t"
echo "  ls /etc/nginx/sites-enabled/"
