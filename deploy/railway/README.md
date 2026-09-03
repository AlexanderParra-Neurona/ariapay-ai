# Railway deploy

Pushes the existing Dockerfile straight to Railway — no VM, no nginx, no certbot.
Railway builds the image, terminates TLS, and assigns a `*.up.railway.app` domain
automatically (a custom domain can be attached after).

The actual Railway config lives at [`railway.json`](../../railway.json) in the repo
root — Railway's CLI/dashboard only auto-detects it there, so it isn't duplicated
under this folder.

## 1. Install the CLI and log in

```bash
brew install railway
railway login   # opens a browser
```

## 2. Link this repo to a Railway project (one-time)

```bash
railway init
```

## 3. Deploy

```bash
railway up
```

Builds from the root `Dockerfile` per `railway.json` (`healthcheckPath: /v1/health`).
Railway auto-detects the container's `EXPOSE 8000` as the target port — no `$PORT`
env var wiring needed in the app itself.

## 4. Set secrets

Railway env vars replace `.env` — nothing is read from a file on the service. Fill
in real staging values in your local `.env` (copy from `.env.example` if needed),
then push all of them in one pass and deploy:

```bash
bash deploy/railway/push_env.sh
```

Reads `.env` line by line, calls `railway variable set KEY=value --skip-deploys`
for each (skipping comments, blank lines, and `APP_PORT` — that's only for local
docker-compose's host port binding, Railway routes its own), then runs `railway up`
once at the end. Pass a different file as `bash deploy/railway/push_env.sh path/to/file`
if needed.

`LLM_PROVIDER` isn't pushed — the Dockerfile bakes `.llm-provider` to `deepinfra`
at build time (Railway can't reach a local Ollama instance, so DeepInfra is the
only provider that makes sense off-VM).

To set/change a single variable without touching the rest:

```bash
railway variable set KEY=value
```

## 5. Smoke test

```bash
railway logs   # tail build/runtime logs, useful if the healthcheck fails
curl -s https://<your-app>.up.railway.app/v1/health
```

## 6. Custom domain (optional)

Attach `staging-ai.ariapay.id` (or another subdomain) via the Railway dashboard
(Settings → Networking → Custom Domain), then point its DNS **CNAME** at the value
Railway gives you.

## Notes

- `--mount=type=cache,...` lines in the root `Dockerfile` need an explicit `id=`
  (e.g. `id=uv-cache`) — Railway's builder rejects the anonymous form that plain
  Docker/BuildKit accepts.
- Redeploying after code changes is just `railway up` again — no separate
  nginx/certbot step, unlike the GCP VM path in [`../gcp/`](../gcp/).
