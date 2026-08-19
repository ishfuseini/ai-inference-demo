---
status: passed
phase: 02-streaming-inference-evidence
score: "6/6 verified"
requirements_verified: 6
requirements_total: 6
human_verification:
  - "Live OpenRouter browser run was not executed because `OPENROUTER_API_KEY` is not set in this shell. Set it and run `uv run python app.py` to perform the external-service smoke."
gaps_found: 0
---

# Phase 02 Verification: Streaming Inference Evidence

## Verdict

Phase 02 requirements `INF-01` through `INF-06` are accounted for with source, test, and browser-smoke evidence. No product/source gaps were found.

Status is `passed` for the implemented local lab slice: the OpenRouter request path is covered by mocked streaming client tests, the UI/controller seam is covered by injected async stream tests, and the actual NiceGUI browser surface was smoke-tested in the missing-key state. A live external OpenRouter call was not run because `OPENROUTER_API_KEY` is unavailable in this shell; that remains a user setup action, not a code gap.

## Requirements evidence

| Requirement | Result | Evidence |
|---|---|---|
| `INF-01`: User can enter or use a prompt and run a live OpenRouter chat completion. | Verified for UI path and request construction; external live smoke requires API key. | `app.py` creates `RunHistory()` and calls `build_app(config, history)`. `src/openrouter_demo/ui.py` renders a prompt textarea, four sample prompt buttons, and `Run Inference`; the click handler rejects blank prompts, checks `config.openrouter_ready`, and calls `_run_inference(..., api_key=os.environ.get(OPENROUTER_API_KEY, ""), strategy=DEFAULT_STRATEGY)`. `tests/test_client.py#test_stream_concatenates_deltas_and_returns_result` verifies the OpenRouter request body/header with `httpx.MockTransport`. Browser smoke with the key unset confirmed `Run Inference` is disabled instead of starting a request. |
| `INF-02`: User can see response text appear progressively while the model streams. | Verified. | `src/openrouter_demo/client.py` yields `StreamChunk` for every SSE delta; `tests/test_client.py#test_stream_concatenates_deltas_and_returns_result` verifies ordered deltas. `src/openrouter_demo/ui.py` wraps the injected stream in `observed_stream`, appends each `StreamChunk.text_delta` to response state, and refreshes the response panel while showing `Streaming from OpenRouter...`. `tests/test_ui.py#test_run_inference_records_successful_stream` verifies concatenated streamed text from multiple chunks. |
| `INF-03`: Completed run displays selected strategy and actual model/provider evidence when available. | Verified. | `src/openrouter_demo/routing.py` defines `DEFAULT_STRATEGY` with name `default`, model `openai/gpt-4o-mini`, and description `Balanced route for general quality and availability.` `src/openrouter_demo/ui.py` renders `Default` and the strategy description, records `strategy_name`, and renders model/provider through telemetry/history helpers. Client tests verify model extraction and provider extraction including `openrouter_metadata`. |
| `INF-04`: Completed run displays observed latency and success/failure state. | Verified. | `src/openrouter_demo/client.py` computes `latency_ms`; `StreamedResult` and `TelemetryEvidence` carry it. `src/openrouter_demo/ui.py` renders `Request completed successfully.`, `Request failed before fallback could complete.`, and latency as `<n> ms`. `tests/test_ui.py#test_run_inference_records_successful_stream` verifies latency copy into telemetry; `tests/test_ui.py#test_run_inference_records_partial_text_on_stream_failure` verifies failed run state. |
| `INF-05`: Completed run displays token and cost metadata when available. | Verified. | `src/openrouter_demo/client.py` extracts prompt/completion/total tokens and cost from `usage`. `tests/test_client.py#test_stream_concatenates_deltas_and_returns_result` verifies token and cost extraction. `src/openrouter_demo/ui.py` renders total tokens via `_format_tokens` and cost via `_format_cost`; `tests/test_ui.py#test_telemetry_and_history_rows_render_unavailable_copy` covers token/cost rendering when unavailable. |
| `INF-06`: UI clearly distinguishes unavailable metadata from zero values. | Verified. | `src/openrouter_demo/models.py` defines `UNAVAILABLE` as a falsey sentinel that is not equal to numeric zero. `tests/test_client.py#test_stream_missing_usage_is_unavailable` verifies missing usage remains `UNAVAILABLE` and not `0`. `src/openrouter_demo/ui.py` renders `Unavailable from selected route/provider.` and `Cost metadata was not returned for this route/provider.` for absent values. Browser smoke confirmed the unavailable copy in the telemetry panel. |

## Must-have cross-check

- Default strategy path: covered by `DEFAULT_STRATEGY`, UI `Default` copy, `_run_inference` strategy recording, and client mock request assertions.
- Streaming path: covered by client SSE chunk tests and UI seam tests; UI response panel refreshes on each `StreamChunk`.
- Telemetry path: covered by `StreamedResult`, `TelemetryEvidence`, UI row helpers, and UI tests.
- Missing metadata honesty: covered by `UNAVAILABLE`, `_format_metadata`, `_format_tokens`, `_format_cost`, tests, and browser smoke.
- Missing credential guard: covered by config readiness, UI disabled button, tests/source contract, and browser smoke.
- Scope control: UI includes no cost/latency/custom controls, fallback simulation, cache/repeat claims, Langfuse trace links, or eval execution controls.

## Automated verification

- `uv run pytest tests/test_ui.py tests/test_client.py -q` -> 11 passed during plan 02-01 verification.
- `uv run pytest` -> 28 passed during plan 02-02 and phase gate verification.
- `uv run ruff check .` -> passed during plan 02-02 and phase gate verification.

## UI verification

Completed on 2026-08-19 against the actual NiceGUI app without external credentials:

1. Started the app with `OPENROUTER_API_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` unset: `env -u OPENROUTER_API_KEY -u LANGFUSE_PUBLIC_KEY -u LANGFUSE_SECRET_KEY -u LANGFUSE_BASE_URL uv run python app.py`.
2. Opened `http://127.0.0.1:8080` in Chromium.
3. Confirmed document title/header `OpenRouter Production Inference Lab`.
4. Confirmed supporting line `A model call is easy. Operating inference is the real problem.`.
5. Confirmed OpenRouter setup guidance: `Set OPENROUTER_API_KEY in your shell, then restart the app.`.
6. Confirmed Langfuse disabled copy: `Langfuse tracing disabled. Configure Langfuse credentials to enable trace links.`.
7. Confirmed all four sample prompts render.
8. Confirmed response empty state, telemetry, run history, and unavailable metadata/cost copy render.
9. Confirmed `RUN INFERENCE` is disabled with `disabled: true` and `aria-disabled: true`.

## Release / next action

No code gap was found for `INF-01` through `INF-06`. To demonstrate the live external-service path, set `OPENROUTER_API_KEY` and run `uv run python app.py`; Phase 03 can add routing/fallback controls on top of the verified default streaming console.
