# Failure Tree - OpenRouter Production Inference Lab

## Purpose

This document describes how to debug a failed or degraded inference request from the app to OpenRouter to the provider and back through telemetry.

The goal is not to list every possible failure. The goal is to show a practical diagnosis path an FDE could use with a customer.

## High-level tree

```text
Request failed or degraded
|
+-- Client / Python
|   +-- malformed request
|   +-- serialization issue
|   +-- streaming parser issue
|   +-- timeout configuration issue
|
+-- Authentication / API
|   +-- missing API key
|   +-- invalid API key
|   +-- rate limit
|   +-- request validation error
|
+-- OpenRouter routing
|   +-- model unavailable
|   +-- provider unavailable
|   +-- routing constraint too narrow
|   +-- fallback not configured
|   +-- fallback configured but not reached
|
+-- Runtime
|   +-- latency spike
|   +-- timeout
|   +-- interrupted stream
|   +-- partial response
|
+-- Observability
|   +-- trace missing
|   +-- token metadata missing
|   +-- cost metadata missing
|   +-- cache metadata missing
|   +-- eval result not recorded
|
+-- Application UI
    +-- response not rendered
    +-- telemetry not displayed
    +-- fallback hidden from user
    +-- missing metadata shown ambiguously
```

## Diagnosis path

### 1. Did the request leave the app correctly?

Check:

- prompt is non-empty
- model/route strategy is valid
- request payload matches OpenRouter-compatible chat completion format
- streaming flag is set when expected
- timeout settings are reasonable

Likely files:

```text
src/openrouter_demo/client.py
src/openrouter_demo/routing.py
```

Common signs:

- immediate client-side exception
- serialization error
- no network request
- request rejected before streaming starts

Next action:

> Log or inspect the normalized request payload without exposing secrets.

### 2. Did authentication/API validation fail?

Check:

- `OPENROUTER_API_KEY` is set
- key is valid
- account has access/credits as needed
- request body uses supported fields
- rate limit response is not being treated as a generic failure

Likely files:

```text
src/openrouter_demo/config.py
src/openrouter_demo/client.py
.env.example
```

User-facing copy (literal — auth and rate-limit failures surface as the generic failure state):

```text
Request failed before fallback could complete.
```

Next action:

> Separate auth, rate-limit, and validation errors. They imply different fixes.

### 3. Did routing constraints prevent a usable route?

Check:

- selected model exists
- provider preference is valid
- route is not over-constrained
- fallback model/provider is configured
- fallback trigger condition is reachable

Likely files:

```text
src/openrouter_demo/routing.py
src/openrouter_demo/scenarios.py
```

Common signs:

- model unavailable
- provider unavailable
- no fallback attempt shown
- same failure repeats across strategies

User-facing copy (literal):

```text
Request failed before fallback could complete.
```

Next action:

> Loosen route constraints or switch to a known-good fallback strategy.

### 4. Did the provider or runtime degrade?

Check:

- request timed out
- latency exceeded threshold
- stream was interrupted
- partial response was received
- retry/fallback behavior preserved the failure details

Likely files:

```text
src/openrouter_demo/client.py
src/openrouter_demo/telemetry.py
```

Common signs:

- partial streamed output
- timeout after initial tokens
- fallback route succeeds
- high latency but successful completion

User-facing copy (literal):

```text
Completed via fallback route after primary route failed.
```

Next action:

> Preserve partial failure context and record both primary and fallback attempts.

### 5. Did fallback work as intended?

Check:

- primary failure was detected
- fallback route was attempted
- fallback route completed or failed visibly
- UI shows both attempts
- telemetry marks fallback status

Likely files:

```text
src/openrouter_demo/scenarios.py
src/openrouter_demo/client.py
src/openrouter_demo/telemetry.py
src/openrouter_demo/ui.py
```

Good fallback state (literal):

```text
Completed via fallback route after primary route failed.
```

Bad fallback state (literal — a generic success that hides the fallback):

```text
Request completed successfully.
```

Why bad:

> It hides that fallback happened, which removes the operator’s ability to debug reliability.

Next action:

> Make fallback visible in response status, telemetry, and run history.

### 6. Is telemetry missing or misleading?

Check:

- trace created when Langfuse credentials are configured
- tracing disabled state shown when credentials are absent
- latency measured locally
- token/cost metadata shown only when available
- unavailable metadata is not displayed as zero
- cache hit/miss is not invented

Likely files:

```text
src/openrouter_demo/telemetry.py
src/openrouter_demo/models.py
src/openrouter_demo/ui.py
```

User-facing copy:

```text
Langfuse tracing disabled. Configure Langfuse credentials to enable trace links.
```

```text
Cost metadata was not returned for this route/provider.
```

```text
No cache metadata returned. Showing observed repeat behavior only.
```

(illustrative example — not a literal UI string)

Next action:

> Treat missing metadata as a first-class state, not a formatting edge case.

### 7. Did the UI hide the real state?

Check:

- response panel updates during streaming
- telemetry panel updates after completion/failure
- run history records failed and fallback attempts
- errors include next debugging steps
- simulated failures are labeled as simulated

Likely file:

```text
src/openrouter_demo/ui.py
```

Common UI failures:

- fallback shown as plain success
- missing cost shown as `$0.00`
- unavailable provider shown as blank
- simulated failure not labeled
- Langfuse disabled state hidden

Next action:

> Make operational state visible even when the generated response succeeds.

## Failure examples

### Missing API key

Symptom:

```text
Request fails immediately.
```

Likely cause:

```text
OPENROUTER_API_KEY is missing or invalid.
```

Fix:

```text
Set OPENROUTER_API_KEY in the environment.
```

### Over-constrained route

Symptom:

```text
The selected strategy fails before producing tokens.
```

Likely cause:

```text
The model/provider preference is unavailable or too narrow.
```

Fix:

```text
Use a less constrained route or configure fallback.
```

### Timeout with fallback success

Symptom:

```text
Primary route fails after waiting, fallback route succeeds.
```

Likely cause:

```text
Provider latency spike or route-specific degradation.
```

Fix:

```text
Record primary failure, use fallback, compare latency and quality before changing defaults.
```

### Missing cost metadata

Symptom:

```text
Response succeeds but cost is unavailable.
```

Likely cause:

```text
Selected route/provider did not return cost metadata in the expected path.
```

Fix:

```text
Show cost as unavailable. Do not display zero unless the actual cost is known to be zero.
```

### Trace missing

Symptom:

```text
Response succeeds but no Langfuse trace link appears.
```

Likely cause:

```text
Langfuse credentials are absent or trace creation failed.
```

Fix:

```text
Keep the app running and show tracing disabled or trace creation failure clearly.
```

## Debugging rule of thumb

Do not collapse distinct failures into “request failed.” Authentication, validation, routing, provider, timeout, telemetry, and UI failures have different fixes.

The demo should make that distinction visible.
