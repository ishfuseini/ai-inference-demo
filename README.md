# OpenRouter Production Inference Lab

A self-contained Python demo that makes production inference behavior visible: how model calls are routed, observed, recovered from failure, and evaluated — with cost, latency, provider, router, cache, and trace evidence, not just the generated text.

## What this demo shows

This is not a chatbot. It is an operating surface for inference: route, observe, recover, and evaluate model calls. Each run surfaces the routing strategy, the model/provider that actually answered, latency, tokens, cost, fallback status, cache/repeat state, and trace state — so a reviewer can see how production inference behaves and fails, then diagnose it.

The five-minute story:

1. **Route** — compare default, cost-oriented, and latency-oriented strategies.
2. **Observe** — watch the response stream and read normalized telemetry.
3. **Recover** — trigger a fallback and keep the failed primary attempt visible.
4. **Evaluate** — run deterministic eval cases and compare quality with evidence.

## Prerequisites

- Python 3.12+
- `uv`

## Install

```bash
uv sync
```

## Configure

Create a local `.env` file or export the four variables below. `OPENROUTER_API_KEY` is required, and the three Langfuse variables are optional. Exported environment variables take precedence over `.env` values.

```bash
cp .env.example .env
# Fill in values in .env, or export them in your shell:
# export OPENROUTER_API_KEY=
# export LANGFUSE_PUBLIC_KEY=
# export LANGFUSE_SECRET_KEY=
# export LANGFUSE_BASE_URL=
```

When `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` are absent, the app launches with tracing visibly disabled rather than blocking.

## Launch

```bash
uv run python app.py
```

If `OPENROUTER_API_KEY` is missing, the page shows setup guidance and does not attempt a live request.

## Five-minute walkthrough

Follow `docs/specs/quickstart.md` for the eight validation steps, and `docs/ux/demo-script.md` for the 30-second pitch and timed five-minute sequence.

## Run the evals

```bash
PYTHONPATH=src uv run python -m openrouter_demo.evals
```

The eval command runs three to five deterministic cases and compares at least two strategies or models with pass/fail reasons, latency, cost/tokens when available, and trace state.

## Quality gates

```bash
uv run pytest
uv run ruff check .
```

## Docs

- `docs/architecture.md` — component boundaries and data flow.
- `docs/content-editing-guide.md` — copy, labels, and documentation voice for future edits.
- `docs/failure-tree.md` — how to debug a failed or degraded request.
