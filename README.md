# OpenRouter Production Inference Lab

A local Python demo for making production inference behavior visible: setup, routing, fallback, cost/latency evidence, repeat/cache observations, deterministic evals, and optional Langfuse tracing.

## Phase 1 status

Implemented now: dependency setup, exported-env inspection, a NiceGUI setup shell, and importable package boundaries.

Not implemented yet: live inference, routing/fallback behavior, telemetry history, cache observations, Langfuse trace creation, and eval execution.

## Prerequisites

- Python 3.12+
- `uv`

## Install

```bash
uv sync
```

## Configure

Use exported environment variables; this app does not parse `.env` files in Phase 1.

```bash
export OPENROUTER_API_KEY=
export LANGFUSE_PUBLIC_KEY=
export LANGFUSE_SECRET_KEY=
export LANGFUSE_BASE_URL=
```

`OPENROUTER_API_KEY` is required for later live inference. Langfuse variables are optional; if they are missing, the app launches and shows tracing as disabled.

## Launch

```bash
uv run python app.py
```

If `OPENROUTER_API_KEY` is missing, the NiceGUI page shows setup guidance and does not attempt a live request.
