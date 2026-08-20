# Phase 4 — API Coverage Matrix

**Phase:** 04 — Telemetry, Repeat, and Observability
**Created:** 2026-08-19
**Gate:** `workflow.api_coverage_gate` (enabled). Default disposition is **INTEGRATE**; every OPT-OUT carries a one-line reason.

## OpenRouter (direct HTTPS Chat Completions)

| Capability | Decision | Notes / Reason |
|------------|----------|----------------|
| Streaming chat completion (`stream: true`) | INTEGRATE | Already live from Phase 2 via `client.stream_chat_completion`; Phase 4 extends extraction, does not rework transport. |
| Router metadata opt-in header (`X-OpenRouter-Metadata: enabled`) | INTEGRATE | Adds the header to the existing `headers` dict in `client.py`; default is disabled so opt-in is required (OBS-02). |
| Router metadata absence handling | INTEGRATE | `openrouter_metadata` is stripped on cache hits and some error classes; capture as `UNAVAILABLE`, never fabricate (OBS-02). |
| Prompt caching fields (`usage.prompt_tokens_details.cached_tokens` / `cache_write_tokens`) | INTEGRATE | The only honest cache signal; keyed on `prompt_tokens_details`, never on latency or router metadata (OBS-03/OBS-04). |
| Provider routing payload (`provider` key from `strategy_payload`) | INTEGRATE | Phase 3 behavior; unchanged in Phase 4. |
| Fallback controls (`allow_fallbacks: false`) | INTEGRATE | Phase 3 two-attempt orchestration; unchanged in Phase 4. |
| Error envelopes (`error` object in stream) | INTEGRATE | Existing `OpenRouterHTTPError`/`OpenRouterAuthError`/`OpenRouterTimeoutError` path; unchanged. |
| Legacy cache field names (`prompt_cache_hit_tokens` / `prompt_cache_miss_tokens`) | OPT-OUT | Superseded by `prompt_tokens_details`; current docs do not document them (Assumption A4). |
| Legacy metadata header (`X-OpenRouter-Experimental-Metadata`) | OPT-OUT | Superseded by `X-OpenRouter-Metadata`; use the documented stable name. |
| `stream_options.include_usage` | OPT-OUT | OpenRouter streams usage on the final chunk without it; flagging as Assumption A1 to re-verify live before Phase 6. |

## Langfuse Python SDK v4 (installed 4.14.4)

| Capability | Decision | Notes / Reason |
|------------|----------|----------------|
| Conditional client construction (`get_client()`) | INTEGRATE | Called only inside a `config.langfuse_ready` branch; never at import time (OBS-05/OBS-06). |
| Unified observation API (`start_as_current_observation(as_type="generation")`) | INTEGRATE | The only supported v4 path; old `trace()`/`generation()`/`span()` methods are removed. |
| Trace ID capture (`observation.trace_id`) | INTEGRATE | Read from the observation wrapper returned by the context manager. |
| Trace URL (`client.get_trace_url(trace_id=...)`) | INTEGRATE | Renders the clickable link; `LANGFUSE_BASE_URL` must be the UI root (Assumption A3). |
| `flush()` | INTEGRATE | Called after the observation block; short-lived app must flush events. |
| Disabled client (missing `LANGFUSE_*`) | INTEGRATE | `trace_status="disabled"`; no client constructed; visible in UI (OBS-06). |
| Trace failure isolation (`try/except`) | INTEGRATE | Trace exception → `trace_status="failed"`; never changes `InferenceRun.status`. |
| `cost_details` parameter | OPT-OUT | Accepted key format ambiguous in 4.14.4 (`Dict[str, float]` vs README `cost_amount`/`cost_currency`) — attach cost via observation `metadata` instead (Pitfall 7 / Assumption A2). |
| `get_trace_context()` helper | OPT-OUT | Absent in installed 4.14.4; use `observation.trace_id` instead. |
| `trace()` / `generation()` / `span()` legacy methods | OPT-OUT | Removed in v4. |

## Summary

- **Integrate:** 13 capabilities across both APIs.
- **Opt-out:** 7 capabilities, each with a one-line reason above (legacy/removed APIs, ambiguous key format, and one flagged assumption A1 to re-verify live).
- **No blocked capabilities.**
