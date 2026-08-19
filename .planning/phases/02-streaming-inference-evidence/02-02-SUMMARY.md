---
phase: 02-streaming-inference-evidence
plan: 02
subsystem: ui
tags: [nicegui, openrouter, streaming, telemetry, run-history]

requires:
  - phase: 02-streaming-inference-evidence
    provides: 02-01 streaming UI state seam
provides:
  - NiceGUI prompt surface wired to default-route streaming inference
  - Response, telemetry, and run-history panels using explicit unavailable copy
affects: [phase-03-routing, phase-04-observability, phase-05-evals]

actuals:
  tokens: 5106
  tasks: 2
  commits: 1

tech-stack:
  added: []
  patterns:
    - NiceGUI refreshable panels for response, telemetry, and history state
    - App-level `RunHistory` instance passed into UI construction

key-files:
  created: []
  modified:
    - app.py
    - src/openrouter_demo/ui.py
    - tests/test_ui.py

key-decisions:
  - "Used only the existing default routing strategy in Phase 02; cost, latency, custom, fallback, cache, trace-link, and eval controls remain out of scope."
  - "Kept live API key retrieval inside the guarded click handler so missing credentials cannot start a request."

patterns-established:
  - "`app.main()` owns runtime history and passes it into `build_app(config, history)`."
  - "Streaming UI wraps the injected stream function to refresh response text on each `StreamChunk` while `_run_inference` records the durable run."

requirements-completed: [INF-01, INF-02, INF-03, INF-04, INF-05, INF-06]
coverage:
  - id: D1
    description: "`Run Inference` is disabled without `OPENROUTER_API_KEY` and wired to the guarded streaming handler when ready."
    requirement: INF-01
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_build_app_preserves_missing_key_guard_and_required_copy"
        status: pass
      - kind: automated_ui
        ref: "browser smoke http://127.0.0.1:8080 with OPENROUTER_API_KEY unset"
        status: pass
    human_judgment: false
  - id: D2
    description: "Response panel has empty, streaming, success, and failure copy while the observed stream refreshes response text."
    requirement: INF-02
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_build_app_preserves_missing_key_guard_and_required_copy"
        status: pass
    human_judgment: false
  - id: D3
    description: "Completed run UI exposes `Default` strategy plus model/provider evidence when available."
    requirement: INF-03
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_run_inference_records_successful_stream"
        status: pass
    human_judgment: false
  - id: D4
    description: "Telemetry UI renders success/failure status and latency in milliseconds."
    requirement: INF-04
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_telemetry_and_history_rows_render_unavailable_copy"
        status: pass
    human_judgment: false
  - id: D5
    description: "Telemetry and history render token and cost fields only when available."
    requirement: INF-05
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_telemetry_and_history_rows_render_unavailable_copy"
        status: pass
    human_judgment: false
  - id: D6
    description: "Unavailable model/provider/token/cost values render explicit copy, not zero-like values or raw sentinel internals."
    requirement: INF-06
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_telemetry_and_history_rows_render_unavailable_copy"
        status: pass
      - kind: automated_ui
        ref: "browser smoke telemetry unavailable copy"
        status: pass
    human_judgment: false

duration: 20min
completed: 2026-08-19
status: complete
---

# Phase 02 Plan 02 Summary

**NiceGUI streaming console submits default-route prompts, shows response/telemetry evidence, and records recent inference runs.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-08-19T16:44:00Z
- **Completed:** 2026-08-19T17:04:01Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Wired `app.main()` to create `RunHistory()` and pass it into `build_app(config, history)`.
- Replaced the Phase 1 disabled shell with prompt controls, four sample prompts, default strategy summary, response panel, telemetry panel, and run history.
- Preserved missing OpenRouter setup guidance and Langfuse disabled copy while keeping later routing/fallback/cache/eval features out.

## Task Commits

1. **Task 1/2: Runtime state and NiceGUI streaming surface** - `6c60e10` (feat)

## Files Created/Modified

- `app.py` - Instantiates runtime `RunHistory` and passes it into the UI.
- `src/openrouter_demo/ui.py` - Builds the Phase 02 streaming operations console and rendering helpers.
- `tests/test_ui.py` - Adds UI copy, metadata rendering, and history row regression coverage.

## Decisions Made

- Default route only in Phase 02. Phase 3 will add cost/latency/custom strategy controls and fallback behavior.
- Browser smoke used the missing-key path because `OPENROUTER_API_KEY` is not set in this shell.

## Deviations from Plan

None - plan executed as written. Live OpenRouter smoke remains environment-dependent and was not run without credentials.

## Issues Encountered

- Pyright cannot resolve NiceGUI in the LSP environment, but project commands run via `uv` and passed. No code change required.

## User Setup Required

Set `OPENROUTER_API_KEY` to exercise live inference in the browser.

## Next Phase Readiness

Phase 03 can add visible cost/latency/custom routing controls and fallback paths on top of the existing default streaming console.

---
*Phase: 02-streaming-inference-evidence*
*Completed: 2026-08-19*
