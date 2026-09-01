# Staging deploy (GCP VM, shared with existing nginx-fronted backend)

Deploys the existing Docker image to the GCP VM on `127.0.0.1:8000`; the VM's existing nginx
(already reverse-proxying another API backend) gets a second server block for the new
staging subdomain, with its own Let's Encrypt cert via certbot.

Qdrant is already managed/external (see `docker-compose.yml`) — nothing to provision for it.

Nothing here needs secrets pasted into chat/tickets — fill placeholders locally and run.

## 1. One-time GCP setup (run on your laptop)

Requires the `gcloud` CLI, authenticated (`gcloud auth login`) with access to the project.

Edit the 4 placeholders at the top of [`gcp_setup.sh`](./gcp_setup.sh) (`PROJECT_ID`, `VM_NAME`,
`ZONE`, `REGION`), then:

```bash
bash deploy/gcp_setup.sh
```

Reserves the VM's external IP as static if not already (this VM's IP was already reserved for
the existing backend's subdomain — the script detects that and skips), and ensures firewall
ports 80/443 are open (likely already open for the existing backend too). Prints the external
IP — create a DNS **A record** for your staging subdomain (e.g. `staging-ai.ariapay.com`)
pointing at it, TTL 300.

## 2. Bootstrap the VM (run once, via SSH)

```bash
gcloud compute ssh VM_NAME --zone=ZONE
```

Then on the VM:

```bash
git clone <this repo> ariabot && cd ariabot
bash deploy/vm_bootstrap.sh   # installs Docker if missing (likely already present)
```

## 3. Configure secrets

```bash
cp .env.example .env
$EDITOR .env   # fill in real DEEPINFRA_API_TOKEN, QDRANT_URL/API_KEY, ARIAPAY_API_URL,
               # LOGIN_*, etc. STAGING_DOMAIN isn't read by the app — only needed below for nginx.
```

`.env` stays on the VM only, never committed — same pattern as local dev.

## 4. Deploy the app container

```bash
bash deploy/vm_deploy.sh
```

Brings up `qdrant-init`, `qdrant-ingest`, `app` — listening on `127.0.0.1:8000` only (not
publicly exposed directly; nginx handles that in the next step).

## 5. Add the nginx site + TLS cert (one-time)

```bash
sudo cp deploy/ariabot.nginx.conf /etc/nginx/sites-available/ariabot
sudo sed -i 's/STAGING_DOMAIN_PLACEHOLDER/staging-ai.ariapay.com/' /etc/nginx/sites-available/ariabot
sudo ln -s /etc/nginx/sites-available/ariabot /etc/nginx/sites-enabled/ariabot
sudo nginx -t && echo "systemctl reload nginx" | sudo sh

# Requires DNS to already resolve to this VM (step 1).
sudo certbot --nginx -d staging-ai.ariapay.com
```

certbot rewrites `/etc/nginx/sites-available/ariabot` in place to add the HTTPS server block
and sets up auto-renewal. Confirm the existing backend's site is untouched:

```bash
sudo nginx -t
ls /etc/nginx/sites-enabled/
```

## 6. Smoke test (run from any external machine, not the VM)

```bash
curl -s https://staging-ai.ariapay.com/v1/health
# {"status":"ok"}

curl -s -X POST https://staging-ai.ariapay.com/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"question": "What is Ariapay?"}'
```

If `/v1/health` doesn't return 200, check, in order: DNS resolves to the VM IP, `sudo nginx -t`
passes, `docker compose ... logs -f app` on the VM shows the container healthy.

## Redeploying after code changes

```bash
git pull
bash deploy/vm_deploy.sh
```

nginx/certbot config doesn't need touching again — only the app container restarts.
