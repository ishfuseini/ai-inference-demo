# Local Demo Interface Contracts

The project exposes local demo surfaces, not a public product API. Contracts define what the
UI and commands must make observable to a reviewer.

## UI Contract: Run Inference

### Inputs

- `prompt`: Required non-empty text.
- `strategy`: One of `default`, `cost`, `latency`, or `custom`.
- Optional deterministic scenario trigger: `normal`, `fallback`, `repeat_cache`, or `eval`.

### Behavior

1. User starts a run.
2. UI enters a running/streaming state.
3. Response text appears progressively when streaming chunks arrive.
4. Telemetry panel updates as fields become known.
5. Run finishes as succeeded or failed.

### Required Output Evidence

- Strategy selected.
- Model/provider when available.
- Observed latency.
- Token usage when available.
- Cost when available.
- Fallback status.
- Cache status or repeat observation.
- Trace status and trace link when available.
- Visible error message when failed.

### Error Contract

- Missing required credential shows setup guidance and does not attempt a live request.
- Missing optional observability credentials show tracing disabled and do not block inference.
- Mid-stream failure preserves partial response and visible error state.
- Unavailable metadata is shown as unavailable, not `0`, `None`, or guessed text.

## UI Contract: Routing and Fallback Demonstration

### Inputs

- `strategy`: `cost` or `latency` for routing comparison.
- `scenario`: `fallback` for reproducible failure/recovery.

### Required Output Evidence

- Preferred route or strategy selected.
- Failure reason or timeout state for the primary route.
- Fallback route attempted.
- Final success/failure state.
- Telemetry for the final result and visible failure evidence for the primary attempt.

### Negative Requirements

- The UI must not hide primary failure after fallback succeeds.
- The UI must not claim real provider outage when using a deterministic simulated failure
  trigger.

## UI Contract: Repeat/Cache Demonstration

### Inputs

- Same or equivalent prompt under one or more strategies.

### Required Output Evidence

- Previous run summary.
- Current run summary.
- Cache metadata when provider/OpenRouter exposes it.
- Observed repeat latency/cost comparison when cache metadata is unavailable.

### Negative Requirements

- The demo must not declare a cache hit unless cache metadata supports it.

## Command Contract: Eval Run

### Command

```sh
uv run python -m openrouter_demo.evals
```

A Makefile alias such as `make eval` may wrap this command, but the uv command is canonical.

### Inputs

- `evals/cases.json` containing three to five deterministic eval cases.
- Required inference credential.
- Optional observability credentials.

### Required Output Evidence

For each eval case:

- Case id and name.
- Pass/fail result.
- Score reason.
- Model/provider when available.
- Latency.
- Cost when available.
- Trace status and trace link when available.

### Exit Behavior

- Exit success when all cases run and results are reported, even if some cases fail scoring.
- Exit failure when setup is invalid, credentials are missing, or the eval runner cannot
  complete the configured cases.

## Command Contract: Quality Gates

### Commands

```sh
uv run pytest
uv run ruff check .
```

### Required Behavior

- Tests cover response/error handling, routing configuration, and eval scoring.
- Ruff runs over the repository without requiring a separate frontend build or service setup.
