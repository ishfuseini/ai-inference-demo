---
phase: 02-streaming-inference-evidence
status: complete
sources:
  - .planning/ROADMAP.md
  - .planning/REQUIREMENTS.md
  - .planning/STATE.md
  - docs/tasks/phase-2-streaming-inference.md
  - docs/PRD.md
  - docs/specs/acceptance-criteria.md
  - docs/specs/data-model.md
  - docs/specs/quickstart.md
  - docs/ux/screen-spec.md
  - docs/ux/ui-ux-plan.md
  - src/openrouter_demo/client.py
  - src/openrouter_demo/models.py
  - src/openrouter_demo/routing.py
  - src/openrouter_demo/history.py
  - src/openrouter_demo/ui.py
  - app.py
created: 2026-08-19
---

# Phase 02 Research: Streaming Inference Evidence

## Planning conclusion

Phase 02 should plan the remaining UI integration slice, not re-add the backend already present in the current checkout.

Evidence:

- `src/openrouter_demo/client.py` already defines `OPENROUTER_CHAT_COMPLETIONS_URL`, typed OpenRouter errors, and `stream_chat_completion(...)` as an async iterator yielding `StreamChunk | StreamedResult`.
- `src/openrouter_demo/models.py` already defines `Status`, `StreamChunk`, `StreamedResult`, `TelemetryEvidence`, and `InferenceRun`, while preserving `UNAVAILABLE`.
- `src/openrouter_demo/routing.py` already defines `RoutingStrategy`, `DEFAULT_STRATEGY`, and `strategy_payload(DEFAULT_STRATEGY)`.
- `src/openrouter_demo/history.py` already defines bounded `RunHistory`.
- `tests/test_client.py` already covers SSE concatenation, missing usage as `UNAVAILABLE`, provider fallback from `openrouter_metadata`, typed auth/HTTP/timeout errors, and partial-text preservation.
- `src/openrouter_demo/ui.py` still renders the Phase 1 shell with disabled `Run Inference` and text saying live inference starts in Phase 2.
- `app.py` calls `build_app(config)` and does not instantiate or pass `RunHistory`.

## OpenRouter implementation facts relevant to planning

- Chat completions use `POST https://openrouter.ai/api/v1/chat/completions`.
- Streaming is requested with `"stream": true`.
- Streaming payloads arrive as SSE `data:` lines.
- SSE comment lines starting with `:` must be ignored before JSON parsing.
- The final streaming chunk can carry usage data.
- Mid-stream failures can arrive as `data:` events with an `error` field; the UI must preserve partial text where the client exposes it.
- Router metadata is opt-in with `X-OpenRouter-Metadata: enabled`; when present on streaming success, `openrouter_metadata` arrives on the final chunk before `[DONE]`.
- Cache hits can omit router metadata; unavailable metadata must not be coerced to zero or a guessed provider/model.

## Phase 02 scope fence

In scope:

- Enable the default-strategy prompt path from the NiceGUI UI.
- Stream response text progressively into the response panel.
- Show status, selected strategy, actual model/provider when available, latency, token usage, and cost when available.
- Append one run-history row per completed or failed run.
- Preserve setup guidance when `OPENROUTER_API_KEY` is missing.
- Keep Langfuse visibly disabled/optional.
- Add focused UI-handler tests using `httpx.MockTransport` or dependency injection; no live OpenRouter call in tests.

Out of scope:

- Cost/latency/custom strategy selection UI.
- Fallback scenario controls or simulated failure toggle.
- Cache/repeat claims.
- Langfuse trace creation or trace links.
- Eval execution.
- Separate frontend or FastAPI product API layer.

## Recommended plan shape

Two executable plans are enough:

1. **02-01 UI streaming state tracer** — add a testable async UI/controller seam, wire `RunHistory` through `app.py`, and prove a mocked stream updates state into `InferenceRun` without browser or live network.
2. **02-02 NiceGUI surface integration** — replace the disabled Phase 1 UI with the Phase 02 operations console: prompt, sample prompts, enabled/disabled run button, streaming response, telemetry cards, and run-history table.

Use wave 1 for `02-01`, wave 2 for `02-02`; the UI surface depends on the testable state seam.

## Validation Architecture

### Automated checks

- `uv run pytest tests/test_client.py tests/test_ui.py -q` after the state/controller plan.
- `uv run pytest tests/test_ui.py tests/test_config.py -q` after the NiceGUI surface plan.
- `uv run pytest` and `uv run ruff check .` before phase closeout.

### Behavioral checks

- With a mocked successful stream, progressive deltas concatenate into the visible streamed text and final `InferenceRun.streamed_text`.
- With missing usage/provider/cost metadata, code stores `UNAVAILABLE` and UI renders exact unavailable copy.
- With a mid-stream client exception carrying partial text, history records `Status.FAILED`, a non-empty `error_message`, and the partial `streamed_text`.
- With `OPENROUTER_API_KEY` absent, the app keeps Phase 1 setup guidance and must not attempt a live request.

### Manual smoke

- Optional live smoke with a real `OPENROUTER_API_KEY`: `uv run python app.py`, enter a small prompt, click `Run Inference`, observe progressively streaming response text, telemetry update, and a history row.
- This live smoke should stay bounded by the default small prompts in `docs/ux/screen-spec.md`.

## Risks and mitigations

- **NiceGUI event handlers are hard to test directly.** Put streaming state mutation into a small async function that can be invoked from tests without `ui.run()`.
- **UI can accidentally stringify `UNAVAILABLE`.** Centralize formatting helpers such as `_format_metadata`, `_format_tokens`, and `_format_cost` in `ui.py` and test them through the UI state handler.
- **Live network in tests would be costly and flaky.** Keep tests on `httpx.MockTransport` or injected stream functions only.
- **Scope creep into Phase 3.** Keep strategy selection fixed to `DEFAULT_STRATEGY` in Phase 02; expose type seams for later strategies without adding controls.
- **Duplicate run clicks.** Disable the button while `is_running` is true and ignore blank prompts.
