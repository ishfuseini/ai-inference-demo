---
phase: 02-streaming-inference-evidence
status: complete
sources:
  - src/openrouter_demo/ui.py
  - app.py
  - src/openrouter_demo/client.py
  - src/openrouter_demo/models.py
  - src/openrouter_demo/history.py
  - tests/test_client.py
  - docs/tasks/phase-2-streaming-inference.md
created: 2026-08-19
---

# Phase 02 Pattern Map

## Current analogs

### NiceGUI shell — `src/openrouter_demo/ui.py`

Pattern:

- `build_app(config: AppConfig) -> None` owns UI construction.
- `_status(label, ready, detail)` creates reusable status cards.
- Layout uses `ui.column`, `ui.row`, `ui.card`, `ui.label`, `ui.textarea`, and `ui.button` with Tailwind/Quasar classes.

Relevant excerpts:

- `ui.page_title("OpenRouter Production Inference Lab")`
- `with ui.column().classes("mx-auto w-full max-w-5xl gap-4 p-6")`
- `ui.button("Run Inference").props("disable")`

Phase 02 implication:

- Keep the single `build_app` ownership boundary but change its signature to accept `RunHistory` and injectable stream dependency where needed for tests.
- Add helper functions in the same file instead of introducing a separate frontend layer.

### App wiring — `app.py`

Pattern:

- `main()` loads config, calls `build_app`, then `ui.run(...)`.

Phase 02 implication:

- Instantiate `RunHistory()` in `main()` and pass it to `build_app(config, history)`.
- Do not move NiceGUI startup into another service.

### Streaming backend — `src/openrouter_demo/client.py`

Pattern:

- `stream_chat_completion(...) -> AsyncIterator[StreamChunk | StreamedResult]` is already the backend seam.
- Typed exceptions derive from `OpenRouterError` and carry `partial_text`.
- Missing provider/model/usage/cost maps to `UNAVAILABLE`.

Phase 02 implication:

- UI should consume this seam rather than reconstruct OpenRouter requests.
- Tests can inject a fake async stream with the same yielded `StreamChunk | StreamedResult` shape.

### Typed run state — `src/openrouter_demo/models.py`

Pattern:

- `Status` enum covers `PENDING`, `STREAMING`, `SUCCEEDED`, `FAILED`, `CANCELLED`.
- `InferenceRun` is frozen and carries prompt, strategy, timestamps, status, text, error, and telemetry.
- `TelemetryEvidence` carries metadata using `Unavailable` sentinel for absent fields.

Phase 02 implication:

- UI state handler should create `InferenceRun` instances rather than loose dictionaries.
- Formatting helpers must render `Unavailable` as user-facing copy.

### Run history — `src/openrouter_demo/history.py`

Pattern:

- `RunHistory.append(run)` and `RunHistory.all()` provide bounded in-memory storage.

Phase 02 implication:

- Reuse as process-local history; do not add persistence, database, or globals.

### Existing tests — `tests/test_client.py`

Pattern:

- Uses `httpx.MockTransport` and local SSE bytes.
- Runs async client calls through `asyncio.run`.
- Tests no live OpenRouter calls.

Phase 02 implication:

- `tests/test_ui.py` should follow the same no-live-call discipline.
- Prefer direct invocation of a small UI state handler over browser automation for automated tests.

## Data flow

```text
app.py
  load_config() -> AppConfig
  RunHistory()
  build_app(config, history)

NiceGUI event handler
  prompt text + DEFAULT_STRATEGY + api key
  -> stream_chat_completion(...)
  -> StreamChunk updates response text
  -> StreamedResult creates TelemetryEvidence + InferenceRun
  -> RunHistory.append(run)
  -> refresh telemetry/history UI
```

## Concrete planner advice

- Create `tests/test_ui.py` first so execution has a red/green contract for UI state behavior.
- Add internal helpers in `ui.py` such as `_format_metadata`, `_format_cost`, `_format_tokens`, and an async handler like `_run_inference(...)` or `_collect_stream(...)`; exact names can vary, but symbols must be listed in PLAN artifacts.
- Keep any dependency injection explicit: pass `stream_fn`/`api_key`/`history` into testable helpers, while `build_app` wires the real `stream_chat_completion` for runtime.
- Use NiceGUI refresh/update patterns; when backgrounding independent coroutines, prefer NiceGUI `background_tasks.create` over raw `asyncio.create_task`.
