# Staging deploy (GCP VM, shared with existing nginx-fronted backend)

Two deploy paths exist:

- **This file** — GCP VM behind the existing shared nginx (`gcp/` for the GCP-specific
  scripts, everything else here is generic Ubuntu/Docker/nginx and reusable on any VM).
- **[`railway/`](./railway/README.md)** — push the same Dockerfile to Railway instead, no
  VM/nginx/certbot to manage.

Deploys the existing Docker image to the GCP VM on `127.0.0.1:${APP_PORT:-8000}`; the VM's
existing nginx (already reverse-proxying another API backend) gets a second server block for
the new staging subdomain, with its own Let's Encrypt cert via certbot. If the existing
backend already occupies port 8000 on the VM, set `APP_PORT` to a free port (e.g. `8001`) in
`.env` in step 3 — nginx just needs to point at the same port (step 5).

Qdrant is already managed/external (see `docker-compose.yml`) — nothing to provision for it.

Nothing here needs secrets pasted into chat/tickets — fill placeholders locally and run.

## 1. One-time GCP setup (run on your laptop)

Requires the `gcloud` CLI, authenticated (`gcloud auth login`) with access to the project.

Edit the 4 placeholders at the top of [`gcp/gcp_setup.sh`](./gcp/gcp_setup.sh) (`PROJECT_ID`, `VM_NAME`,
`ZONE`, `REGION`), then:

```bash
bash deploy/gcp/gcp_setup.sh
```

Reserves the VM's external IP as static if not already (this VM's IP was already reserved for
the existing backend's subdomain — the script detects that and skips), and ensures firewall
ports 80/443 are open (likely already open for the existing backend too). Prints the external
IP — create a DNS **A record** for your staging subdomain (e.g. `staging-ai.ariapay.id`)
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

Brings up `app` — listening on `127.0.0.1:${APP_PORT:-8000}`
only (not publicly exposed directly; nginx handles that in the next step). The script prints
the actual port it bound.

## 5. Add the nginx site + TLS cert (one-time)

Requires DNS to already resolve to this VM (step 1).

```bash
STAGING_DOMAIN=staging-ai.ariapay.id APP_PORT=8000 bash deploy/vm_nginx_setup.sh
```

Copies [`ariabot.nginx.conf`](./ariabot.nginx.conf) into `sites-available`, fills in the domain
and port, enables the site, reloads nginx, then runs certbot. certbot rewrites
`/etc/nginx/sites-available/ariabot` in place to add the HTTPS server block and sets up
auto-renewal. The script is safe to re-run (skips steps already done) and prints commands at
the end to confirm the existing backend's site is untouched.

## 6. Smoke test (run from any external machine, not the VM)

```bash
curl -s https://staging-ai.ariapay.id/v1/health
# {"status":"ok"}

curl -s -X POST https://staging-ai.ariapay.id/v1/chat \
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
