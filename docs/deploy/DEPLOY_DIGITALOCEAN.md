# Deploying the demo to DigitalOcean App Platform (Direct from repo)

This guide explains how to deploy the OpenRouter Production Inference Lab demo directly from the repository to DigitalOcean App Platform. It covers environment variables, recommended App Platform settings, a quick local smoke test, and guidance on the demo's SQLite store.

NOTE: This repo is intended for demo and reviewer use. For production-grade deployments consider using a managed DB/Redis and container images.

## Prerequisites

- A DigitalOcean account and App Platform access
- A repository fork or access to this repository
- Optional: OPENROUTER API key for live inference, Langfuse keys for optional tracing
- Python runtime >= 3.12 (the project requires >=3.12)

## What to deploy

Deploy the repository root. The app entrypoint is `app.py` and the project uses `uv` as the development/project runner. For direct-from-repo deploys the simplest approach is to let DO's Python buildpack run project setup and use `uv` in the start command so the runtime matches local development.

## Environment variables (required / optional)

- Required for live inference:
  - OPENROUTER_API_KEY — API key used for live OpenRouter requests.

- Optional (tracing):
  - LANGFUSE_PUBLIC_KEY
  - LANGFUSE_SECRET_KEY
  - LANGFUSE_BASE_URL

Note: If you do not set OPENROUTER_API_KEY the app launches and shows setup guidance — it will not attempt live inference.

## App Platform settings (recommended)

1. Create a new App on DigitalOcean App Platform and connect the repository.
2. Choose the `main` branch (or a branch you prefer).
3. Build & Run configuration:
   - Build command: `uv sync -q`  
     (This ensures the uv-managed environment installs dev/runtime deps.)
   - Run command: `uv run python app.py`  
     (This runs the app with the same uv-managed interpreter used locally.)
4. Instance size: a small instance is fine for demo (e.g., Basic-xxs / cheapest tier).
5. HTTP route and health check:
   - App Platform default HTTP route (root path `/`) is fine; the NiceGUI app responds at `/`.
   - Configure a health check that GETs `/` or an explicit readiness endpoint if you add one.
6. Environment variables / secrets:
   - Add `OPENROUTER_API_KEY` under the App's environment settings. Mark it as a secret.
   - Optionally add Langfuse keys (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`) as secrets.

## Data & persistence

- The demo creates a local SQLite DB at `data/runs.db` for recent-run persistence. The file is ignored by Git via `.gitignore`.
- App Platform provides ephemeral storage for the container; the DB will persist for the life of the instance but is not shared between instances. For a single-instance demo this is acceptable.
- If you need persistence across restarts or multiple instances, use a managed DB (Postgres) or Redis for the recent-run store. The code is currently structured to allow swapping stores (in-memory -> SQLite -> Redis/DB).

## Local smoke test (before pushing to DO)

1. Copy `.env.example` to `.env` and fill in secrets (do NOT commit `.env`).
2. Export env vars into your shell:

```bash
set -a; source .env; set +a
# or export manually:
# export OPENROUTER_API_KEY="sk_live_..."
```

3. Create the project environment and run the app using `uv`:

```bash
uv sync -q
uv run python app.py
```

4. Visit the app at `http://localhost:8080` (NiceGUI default) and run a sample prompt. If OPENROUTER_API_KEY is missing you'll see setup guidance instead of an attempted live call.

## Health checks & readiness

- The default root `/` served by NiceGUI is sufficient as a health check for demo use.
- If you want a lightweight readiness endpoint, add a small `/health` route that returns HTTP 200 when the app starts and the config readiness is loaded.

## Security and secrets

- Never commit API keys or `.env` to the repo.
- Use App Platform's environment secrets feature to store `OPENROUTER_API_KEY` and Langfuse keys.
- For CI, store secrets in your CI environment's secret store and avoid exposing them in logs.

## Optional: Using Docker (alternative)

If you prefer reproducible builds, create a small Dockerfile and deploy the built image to App Platform. The Docker approach is more portable but for a demo the direct-from-repo method is simplest.

## Troubleshooting

- If the app fails to start on DO, check build logs for missing commands — ensure `uv` is available during build by running `uv sync` in the build step.
- If run history appears empty, verify `data/runs.db` was created and has write permissions. Check DO's instance disk persistence guarantees for your chosen plan.

## Next steps after deploy

- Optionally add a DO-managed Postgres or Redis for resilient persistence.
- Enable Langfuse tracing by setting Langfuse env vars and verifying trace IDs appear in the run records.

---

If you'd like, I can:
- Add a simple `/health` endpoint to the app before deployment.
- Add DO-specific step-by-step screenshots or a one-click App spec.
- Create a Dockerfile and an alternate deployment guide for image-based deployment.

Tell me which of these you'd like next.