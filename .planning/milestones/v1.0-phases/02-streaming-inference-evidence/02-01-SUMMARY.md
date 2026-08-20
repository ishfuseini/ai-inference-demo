---
phase: 02-streaming-inference-evidence
plan: 01
subsystem: ui
tags: [nicegui, openrouter, streaming, telemetry, pytest]

requires:
  - phase: 01-runnable-skeleton-and-config
    provides: Runnable NiceGUI app shell and config readiness checks
provides:
  - Testable UI handler that converts streamed OpenRouter events into durable inference runs
  - Explicit unavailable metadata, token, and cost formatting helpers
affects: [phase-02-ui, routing-demo, telemetry-panel]

actuals:
  tokens: 2417
  tasks: 2
  commits: 1

tech-stack:
  added: []
  patterns:
    - Inject async stream functions into UI handlers for no-network tests
    - Preserve UNAVAILABLE metadata until explicit copy formatting

key-files:
  created:
    - tests/test_ui.py
  modified:
    - src/openrouter_demo/ui.py

key-decisions:
  - "Kept the streaming seam in `ui.py` because it is UI-owned state orchestration, not client request construction."
  - "Used injected async streams in tests so Phase 02 coverage cannot call live OpenRouter."

patterns-established:
  - "UI state handlers accept injected async streams and append terminal `InferenceRun` objects to `RunHistory`."
  - "Unavailable model/provider/token/cost evidence stays as `UNAVAILABLE` until rendered by format helpers."

requirements-completed: [INF-01, INF-02, INF-03, INF-04, INF-05, INF-06]
coverage:
  - id: D1
    description: "A non-empty prompt can start a UI-owned streaming handler with `DEFAULT_STRATEGY` and an API key."
    requirement: INF-01
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_ui.py tests/test_client.py -q"
        status: pass
    human_judgment: false
  - id: D2
    description: "Stream chunks become accumulated response text and a succeeded `InferenceRun`."
    requirement: INF-02
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_run_inference_records_successful_stream"
        status: pass
    human_judgment: false
  - id: D3
    description: "Terminal stream metadata is copied into `TelemetryEvidence` and unavailable metadata stays sentinel-backed."
    requirement: INF-03
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_run_inference_preserves_unavailable_metadata"
        status: pass
    human_judgment: false
  - id: D4
    description: "Successful and failed runs record status, latency when available, partial text, and error copy."
    requirement: INF-04
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_run_inference_records_successful_stream; tests/test_ui.py#test_run_inference_records_partial_text_on_stream_failure"
        status: pass
    human_judgment: false
  - id: D5
    description: "Token and cost fields are preserved only when stream metadata supplies them."
    requirement: INF-05
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_run_inference_preserves_unavailable_metadata"
        status: pass
    human_judgment: false
  - id: D6
    description: "Missing evidence never renders as zero, empty string, None, or raw sentinel text."
    requirement: INF-06
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_run_inference_preserves_unavailable_metadata"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-08-19
status: complete
---

# Phase 02 Plan 01 Summary

**Streaming UI state seam turns injected OpenRouter stream events into response text, telemetry evidence, and bounded run history records.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-08-19T16:44:00Z
- **Completed:** 2026-08-19T16:59:49Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `_run_inference` to consume `StreamChunk` and `StreamedResult` events with an injectable async stream function.
- Added `_format_metadata`, `_format_tokens`, and `_format_cost` so unavailable evidence renders as honest copy instead of zero-like values.
- Added no-network UI seam tests for success, missing metadata, blank prompts, and mid-stream OpenRouter failure with partial text.

## Task Commits

1. **Task 1/2: UI streaming seam and tests** - `0755f35` (feat)

## Files Created/Modified

- `src/openrouter_demo/ui.py` - Adds stream event handling, telemetry mapping, history append, and metadata formatting helpers.
- `tests/test_ui.py` - Covers injected streaming success, unavailable metadata, failure partial text, and blank-prompt rejection.

## Decisions Made

- Kept stream orchestration in `ui.py`; `client.py` still owns OpenRouter request construction and SSE parsing.
- Used injected fake streams for tests; no test instantiates `httpx.AsyncClient` or calls OpenRouter.

## Deviations from Plan

None - plan executed as written.

## Issues Encountered

- Ruff required timezone-aware datetimes and sorted imports; fixed before committing.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 02-02 can wire this seam into the NiceGUI page with live controls, progressive response display, telemetry panels, and run history.

---
*Phase: 02-streaming-inference-evidence*
*Completed: 2026-08-19*
