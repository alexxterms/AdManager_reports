Deployment to Railway — GrowRev Weekly Report

Overview

This project listens for Slack messages from a specific user, parses weekly metrics, renders a PDF report (via Playwright) in-memory, and uploads the PDF to Slack. This README explains how to deploy the pipeline to Railway using the provided Dockerfile (recommended) or via Git integration.

What I'll cover

- Required environment variables
- Railway service type & recommended resources
- Deploy using GitHub integration (Railway) or Docker image
- Local Docker commands to test the container
- Notes and troubleshooting

Required environment variables (set these in Railway - Environment tab)

- SLACK_BOT_TOKEN — Slack bot token (xoxb-...)
- SLACK_APP_TOKEN — Slack app-level token (xapp-...)
- SLACK_SIGNING_SECRET — Slack signing secret
- SLACK_AD_MANAGER_USER_ID — Slack user ID the bot should accept submissions from
- SLACK_ALLOWED_CHANNEL_IDS — optional comma-separated channel IDs (empty = allow any)
- SLACK_DM_RECIPIENT_IDS — comma-separated user ids for any DM notifications
- TIMEZONE — (optional) e.g. "Asia/Kolkata"
- PDF_TEMPLATE_PATH — path to your PDF template in the container (defaults to the repo path name configured in `src/config.py`)
- OUTPUT_DIR — directory for output (we no longer write PDFs to disk by default but keep for compatibility; default `output`)
- IDEMPOTENCY_DB_PATH — path to idempotency DB (default `state/idempotency.db`)
- FX_API_URL — currency API URL (defaults to https://open.er-api.com/v6/latest/CAD)
- FX_API_KEY — optional FX API key
- FX_API_TIMEOUT_SECONDS — (optional) default 10
- FX_CACHE_TTL_SECONDS — (optional) default 1800
- GROQ_API_KEY — optional (if using Groq insight service)
- GROQ_MODEL — model name if Groq used (default set in code)
- PDF_FIELD_COORDS_JSON — optional JSON mapping for PDF field coords (default provided)

Notes on `IDEMPOTENCY_DB_PATH` and history DBs

- The app uses SQLite files for idempotency and metrics history. In Railway, you can store these on the container filesystem (ephemeral) or use an external persistent volume. If you want persistence across deploys, consider attaching a persistent volume.

Railway Service Type & Resource Guidance

- Service type: **Worker** (not HTTP) — the app uses Slack Socket Mode and runs continuously.
- Minimum recommended resources for Playwright:
  - 1 vCPU, 2 GB RAM — *may* be sufficient but could be slow launching browsers on cold starts.
  - Recommended: **2 vCPU, 4 GB RAM** for reliable performance and lower latency when Playwright launches Chromium.
- Concurrency: Keep a single worker for simplicity. If you expect many simultaneous reports, scale horizontally.

Deployment Options

Option A — GitHub integration (recommended)
1. Push your repo to GitHub.
2. In Railway, create a new project → Add a service → Deploy from GitHub.
3. Choose your repository and branch.
4. Railway will detect `Dockerfile` and build the image.
5. In the service settings, set the start command to the default `worker: python -m src.app` via the `Procfile` or simply ensure Railway runs the container's CMD.
6. Add Environment Variables (see list above).
7. Deploy. Monitor logs in Railway to verify Slack socket connects.

Option B — Build & deploy Docker image manually
1. Build image locally or in CI:

```bash
docker build -t growrev-reports:latest .
# Optional: push to a registry
docker tag growrev-reports:latest ghcr.io/<your-org>/growrev-reports:latest
docker push ghcr.io/<your-org>/growrev-reports:latest
```

2. In Railway, create a new service and choose "Deploy from Docker image" and point to your image in the registry.
3. Set environment variables as above.

Local Docker test commands

Build the image locally (from repo root):

```bash
docker build -t growrev-reports:local .
```

Run the container with environment variables from `.env` (local testing):

```bash
# Create .env locally with the variables (do NOT commit .env to git)
# Then run:
docker run --rm --env-file .env -p 3000:3000 --name growrev-local growrev-reports:local
```

(Port binding is optional — the app is a worker but binding won't hurt.)

Railway-specific quick steps (GitHub deploy)

1. Create Railway account and install Railway CLI (optional):
   - https://railway.app/
   - `npm i -g railway` (optional)
2. From Railway dashboard → New Project → Deploy from GitHub → select repo → Deploy
3. Set environment variables in the Railway project settings
4. Allocate resources (2 vCPU, 4 GB RAM recommended)
5. Start service and watch logs

What to watch in the logs

- "Listening for messages from user" — bot started and connected
- "Converted metrics message delivered" — parsed message succeeded
- "PDF report generated (NNN bytes)" — PDF rendered in-memory
- "PDF report uploaded for event" — Slack upload successful

Troubleshooting & Tips

- If Playwright fails to launch on Railway, ensure the Docker base image includes system dependencies; the provided `mcr.microsoft.com/playwright/python:latest` base image usually contains them.
- If you see permission issues with SQLite files, consider setting `IDEMPOTENCY_DB_PATH` to a folder Railway exposes or use an external DB service.
- Cold-start time includes Playwright browser launch; to reduce latency consider a warm-up ping, or keep a small always-on worker instance.

Next steps I can take for you

- Add a `README_DEPLOY_RAILWAY.md` (this file) to the repo (done).
- Add Railway `Service` template if you want a GitHub action or `.railway` settings file.
- Help set up GitHub → Railway connection, or build and push a Docker image for you.

