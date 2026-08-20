---
phase: 02-streaming-inference-evidence
status: complete
selected_framework: direct-openrouter-httpx
sources:
  - docs/PRD.md
  - docs/tasks/phase-2-streaming-inference.md
  - docs/specs/data-model.md
  - src/openrouter_demo/client.py
  - src/openrouter_demo/routing.py
  - src/openrouter_demo/models.py
  - tests/test_client.py
created: 2026-08-19
---

# Phase 02 AI-SPEC: Direct OpenRouter Streaming

## Selected approach

Use direct OpenRouter Chat Completions requests over HTTPS through `httpx`. Do not introduce an OpenAI SDK, OpenRouter SDK wrapper, LangChain, another router, or a separate backend service in Phase 02.

The NiceGUI UI calls project-owned code in `openrouter_demo.client` and `openrouter_demo.routing`; OpenRouter-specific request bodies, headers, SSE parsing, and metadata handling remain inspectable.

## Boundary contract

- Endpoint: `https://openrouter.ai/api/v1/chat/completions`.
- Request body includes `model`, `messages`, and `stream: true`.
- Authentication header is `Authorization: Bearer <OPENROUTER_API_KEY>`.
- Content header is `Content-Type: application/json`.
- Router metadata may be requested with `X-OpenRouter-Metadata: enabled` when needed for provider/routing evidence.
- Phase 02 uses `DEFAULT_STRATEGY` only in the UI; additional strategy controls are Phase 03.

## Streaming event contract

- Content deltas from `choices[0].delta.content` append to visible response text.
- Final result carries full concatenated text plus model/provider/usage/cost/latency evidence when available.
- SSE comments beginning with `:` are ignored by the client.
- Mid-stream error payloads are treated as failures while preserving partial text through the typed client exception.

## Metadata honesty

- Missing model, provider, token, or cost metadata remains `UNAVAILABLE` in Python data.
- UI renders `UNAVAILABLE` as explicit copy, not `0`, `0.0`, `""`, `None`, or raw `Unavailable(label='unavailable')`.
- Required UI copy:
  - `Unavailable from selected route/provider.`
  - `Cost metadata was not returned for this route/provider.`

## Failure taxonomy

- Auth failure: typed `OpenRouterAuthError`; UI should say authentication failed and point to `OPENROUTER_API_KEY`.
- Rate limit/HTTP failure: typed `OpenRouterHTTPError`; UI should show status/failure and preserve any partial text.
- Timeout/transport failure: typed `OpenRouterTimeoutError` or `OpenRouterError`; UI records failure and does not clear partial output.
- Missing API key: no request is attempted; setup guidance stays visible.

## Eval and test strategy

- Unit/integration tests must use `httpx.MockTransport` or injected async stream functions.
- No test may call live OpenRouter.
- Test successful SSE with usage, successful SSE without usage, and mid-stream failure with partial text.
- Optional manual live smoke can use a small prompt and real `OPENROUTER_API_KEY`, but this is not required for automated CI.

## Safety and cost constraints

- Default prompts stay short and production-style.
- No secret value is rendered in UI or committed to docs/examples.
- Langfuse remains disabled/out-of-scope for Phase 02; missing Langfuse credentials must not block live OpenRouter inference.
- Do not add fallback, cache, eval, or trace claims before those phases implement evidence.
