# Deploying the demo to Fly.io

This guide explains how to deploy the OpenRouter Production Inference Lab to Fly.io — a global PaaS that runs full Python processes with persistent volumes, WebSocket support, and automatic HTTPS.

The app uses NiceGUI (a server-side UI framework with WebSocket connections), httpx for async OpenRouter calls, and a local SQLite database for run history. Fly.io supports all of these natively.

> **NOTE:** This repo is intended for demo and reviewer use. Fly.io's free allowance covers a small shared-CPU machine with a 1 GB volume for single-instance demo use.

---

## Prerequisites

- A [Fly.io](https://fly.io) account
- `flyctl` CLI installed — see [installation guide](https://fly.io/docs/hands-on/install-flyctl/)
- Python 3.12+ and `uv` available locally for smoke testing
- Optional: `OPENROUTER_API_KEY` for live inference, Langfuse keys for optional tracing

Install flyctl on macOS:

```bash
brew install flyctl
```

---

## What to deploy

Deploy the repository root. The app entrypoint is `app.py`, which starts a NiceGUI server on port 8080. The project uses `uv` for dependency management.

### Files created by this guide

| File | Purpose |
|------|---------|
| `Dockerfile` | Container image definition for Fly.io |
| `fly.toml` | Fly.io app configuration (region, port, volume, health checks) |

---

## Step 1: Create the Dockerfile

Create `Dockerfile` in the repo root:

```dockerfile
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (cached layer)
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/
COPY app.py evals/ data/ ./

# Expose the port NiceGUI listens on
EXPOSE 8080

# Run the app — uv runs in the project's virtualenv automatically
CMD ["uv", "run", "python", "app.py"]
```

> **Note:** If there is no `uv.lock` file, remove the `--frozen` flag and the `uv.lock*` glob from the COPY line.

---

## Step 2: Update app.py for port binding

NiceGUI's `ui.run()` defaults to port 8080, which matches Fly.io's `internal_port`. However, to be explicit and ensure the app binds to `0.0.0.0` (required by Fly.io), update the `ui.run()` call in `app.py`:

```python
ui.run(
    title="OpenRouter Production Inference Lab",
    reload=False,
    host="0.0.0.0",
    port=8080,
)
```

If `PORT` environment variable support is needed (e.g. for other platforms), use:

```python
import os
port = int(os.environ.get("PORT", 8080))
ui.run(title="OpenRouter Production Inference Lab", reload=False, host="0.0.0.0", port=port)
```

---

## Step 3: Create fly.toml

Create `fly.toml` in the repo root:

```toml
app = "openrouter-inference-lab"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[http_service.checks]
  interval = "15s"
  timeout = "5s"
  grace_period = "30s"
  method = "GET"
  path = "/health"
  headers = { X-Forwarded-Proto = "https" }

[mounts]
  source = "run_data"
  destination = "/app/data"
  auto_extend_size_threshold = 80
  auto_extend_size_increment = "1GB"
  auto_extend_size_limit = "10GB"
```

### Configuration notes

| Setting | Value | Why |
|---------|-------|-----|
| `app` | `openrouter-inference-lab` | Globally unique app name on Fly.io — change to your own |
| `primary_region` | `iad` | US East (Ashburn, VA). Choose the region closest to you — see `fly platform regions` |
| `internal_port` | `8080` | Must match the port in `app.py` |
| `auto_stop_machines` | `true` | Stops the machine when idle to save free allowance |
| `auto_start_machines` | `true` | Starts the machine when a request arrives |
| `mounts.source` | `run_data` | Persistent volume name — created in Step 5 |
| `mounts.destination` | `/app/data` | Where the SQLite DB (`runs.db`) lives |
| Health check path | `/health` | The app exposes a `/health` endpoint for readiness checks |

---

## Step 4: Launch the app

```bash
# Log in to Fly.io
fly auth login

# Launch (creates the app on Fly.io without deploying yet)
fly launch --no-deploy
```

`fly launch` will:
- Detect the `Dockerfile` and `fly.toml`
- Ask you to confirm the app name and region
- Create the app on Fly.io

---

## Step 5: Create a persistent volume

The SQLite database (`data/runs.db`) needs a persistent volume to survive machine restarts:

```bash
# Create a 1 GB volume named "run_data" in your primary region
fly volumes create run_data --region iad --size 1
```

> If you chose a different `primary_region` in `fly.toml`, use that region here too.

---

## Step 6: Set secrets

Set environment variables as Fly.io secrets (never commit these to the repo):

```bash
# Required for live inference
fly secrets set OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Optional: Langfuse tracing
fly secrets set LANGFUSE_PUBLIC_KEY=your-public-key
fly secrets set LANGFUSE_SECRET_KEY=your-secret-key
fly secrets set LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

> If you skip `OPENROUTER_API_KEY`, the app still launches and shows setup guidance — it will not attempt live inference.

---

## Step 7: Deploy

```bash
fly deploy
```

Fly.io builds the Docker image, provisions the machine, attaches the volume, and routes traffic. The first deploy takes 2–5 minutes.

Once deployed, open the app:

```bash
fly apps open
```

Or visit `https://openrouter-inference-lab.fly.dev` (substituting your app name).

---

## Post-deploy verification

| Check | Command | Expected |
|-------|---------|----------|
| Machine running | `fly status` | `status=running` |
| Health endpoint | `curl https://<app>.fly.dev/health` | `{"status":"ok","openrouter_ready":true,...}` |
| App loads | `fly apps open` | NiceGUI UI renders in browser |
| Logs | `fly logs` | No errors, startup messages visible |

---

## Data & persistence

- The demo creates a local SQLite DB at `/app/data/runs.db` (inside the mounted volume).
- The volume persists across machine restarts and deploys.
- For a single-instance demo this is sufficient. Multi-instance deployments would require an external database (e.g. Fly Postgres or LiteFS) — not needed for this demo.

---

## Common operations

```bash
# View live logs
fly logs

# SSH into the running machine
fly ssh console

# Restart the app
fly apps restart openrouter-inference-lab

# Scale to a different machine size
fly scale vm shared-cpu-1x

# Destroy the app (removes everything including volumes)
fly apps destroy openrouter-inference-lab
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `fly deploy` fails with build error | Missing `uv.lock` or wrong Python version | Remove `--frozen` from Dockerfile, ensure `pyproject.toml` is correct |
| App loads but shows setup guidance | `OPENROUTER_API_KEY` not set | Run `fly secrets set OPENROUTER_API_KEY=...` then `fly deploy` |
| Health check fails | App not listening on port 8080 | Verify `ui.run(port=8080, host="0.0.0.0")` in `app.py` |
| SQLite DB resets on restart | Volume not attached | Verify `[mounts]` in `fly.toml` and `fly volumes list` shows the volume |
| WebSocket errors in browser | Fly.io proxy not forwarding WS | Ensure `force_https = true` in `fly.toml` (Fly.io handles WS upgrade) |

---

## Cost estimate

| Resource | Fly.io free allowance | This app uses |
|----------|----------------------|---------------|
| Shared-CPU 1x, 256 MB | 3 shared-cpu-x1@256MB VMs free | 1 VM (auto-stops when idle) |
| Volume storage | 3 GB free | 1 GB |
| Outbound bandwidth | 160 GB/month free | Minimal (demo traffic) |

**Expected cost: $0/month** for a single-instance demo within the free allowance.
