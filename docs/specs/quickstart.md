# Quickstart: OpenRouter Inference Lab

This guide proves the feature end-to-end from a clean checkout. It intentionally keeps the
runtime path local and small.

## Prerequisites

- Python 3.12+
- `uv`
- An OpenRouter API key
- Optional Langfuse public/secret keys and base URL

## 1. Install dependencies

```sh
uv sync
```

Expected outcome: dependencies install and the project environment is ready.

## 2. Configure credentials

Create a local environment file or export variables in your shell:

```sh
export OPENROUTER_API_KEY="..."
# Optional tracing:
export LANGFUSE_PUBLIC_KEY="..."
export LANGFUSE_SECRET_KEY="..."
export LANGFUSE_BASE_URL="..."
```

Expected outcome:

- With `OPENROUTER_API_KEY`, live inference can run.
- Without Langfuse variables, the app still runs and marks tracing disabled.
- No secret values are committed; `.env.example` documents variable names only.

## 3. Start the local demo UI

```sh
uv run python app.py
```

Expected outcome: a local NiceGUI page opens or prints a local URL.

## 4. Validate User Story 1: streaming inference

1. Enter a short prompt such as `Explain eventual consistency in two paragraphs`.
2. Select the default strategy.
3. Run inference.

Expected outcome:

- Response text appears progressively.
- Completed run shows strategy, model/provider when available, latency, success/failure
  state, fallback status, trace status, and token/cost/cache-or-repeat fields when available.
- Unavailable metadata is labeled unavailable.

## 5. Validate User Story 2: routing and fallback

1. Run the same prompt with the cost-oriented strategy.
2. Run the same prompt with the latency-oriented strategy.
3. Trigger the fallback scenario.

Expected outcome:

- Strategy changes are visible in the telemetry panel.
- Fallback scenario shows preferred route, primary failure or timeout reason, fallback route,
  final state, and telemetry.
- Primary failure evidence remains visible after fallback succeeds.

## 6. Validate User Story 3: repeat/cache and eval comparison

1. Run the repeat/cache scenario with the same or equivalent prompt.
2. Run the eval command:

```sh
uv run python -m openrouter_demo.evals
```

Expected outcome:

- Repeat/cache view reports provider cache metadata only when available.
- If cache metadata is unavailable, the demo reports observed repeat latency/cost instead.
- Eval command completes three to five cases with deterministic pass/fail result, score
  reason, latency, model/provider when available, cost when available, and trace status.

## 7. Validate User Story 4: interview walkthrough

Read the primary guide and failure tree:

```sh
# Files expected after implementation
README.md
docs/failure-tree.md
docs/architecture.md
```

Expected outcome:

- The project story is understandable in 30 seconds.
- The demo sequence is runnable in five minutes after setup.
- Failure tree covers client/request, credentials, OpenRouter/provider routing, timeout,
  telemetry, and UI display failure classes.

## 8. Run quality gates

```sh
uv run pytest
uv run ruff check .
```

Expected outcome:

- Focused tests pass for response/error handling, routing configuration, telemetry/eval
  scoring paths.
- Ruff reports no lint failures.

## Troubleshooting expectations

- Missing `OPENROUTER_API_KEY`: app shows setup guidance and does not attempt live requests.
- Missing Langfuse variables: app runs with tracing disabled.
- Provider metadata absent: display says unavailable.
- Provider outage or timeout: failure remains visible and fallback behavior is inspectable.
- Live cost concern: use default small prompts and stop after the documented scenarios.
