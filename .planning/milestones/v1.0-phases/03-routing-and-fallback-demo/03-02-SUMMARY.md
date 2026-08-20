---
phase: 03-routing-and-fallback-demo
plan: 02
subsystem: api
tags: [fallback, orchestration, scenarios, openrouter, nicegui]

requires:
  - phase: 03-routing-and-fallback-demo
    plan: 01
    provides: AttemptRecord, FallbackEvidence, Status.FALLBACK_SUCCEEDED, FALLBACK_PRIMARY_STRATEGY, STRATEGIES
provides:
  - run_fallback_scenario async generator and FallbackResult dataclass
  - _run_fallback_inference UI handler
  - simulate_failure switch in UI
  - fallback evidence rendering in telemetry panel
  - tests for fallback scenario orchestration and evidence rendering
affects:
  - Phase 4+ (repeat/cache scenarios reuse the two-attempt orchestration pattern)

actuals:
  tokens: 4600
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Client-side two-attempt fallback orchestration: primary (deterministic failure) then fallback (real strategy), both recorded as AttemptRecord"
    - "Dual-stream injected test pattern: call_count counter distinguishes primary vs fallback stream invocation"

key-files:
  created:
    - tests/test_scenarios.py
  modified:
    - src/openrouter_demo/scenarios.py
    - src/openrouter_demo/ui.py
    - tests/test_ui.py
    - tests/test_imports.py

key-decisions:
  - "FallbackResult.fallback is StreamedResult | None (None only when primary unexpectedly succeeds)"
  - "Fallback attempt does NOT catch OpenRouterError — if it fails, the exception propagates to the UI handler"
  - "run_fallback_scenario primary error message carries status code (matches client.py's real error format)"

patterns-established:
  - "Dual-stream test injection: a single async generator with call_count branches primary (raise) vs fallback (yield)"

requirements-completed:
  - ROUTE-04
  - ROUTE-05
  - ROUTE-06

coverage:
  - id: D1
    description: "run_fallback_scenario performs two-attempt orchestration with deterministic primary failure"
    requirement: ROUTE-04
    verification:
      - kind: unit
        ref: "tests/test_scenarios.py#test_fallback_scenario_primary_fails_fallback_succeeds"
        status: pass
      - kind: unit
        ref: "tests/test_scenarios.py#test_fallback_scenario_primary_unexpectedly_succeeds"
        status: pass
    human_judgment: false
  - id: D2
    description: "Fallback evidence preserves primary failure and fallback success as AttemptRecords"
    requirement: ROUTE-05
    verification:
      - kind: unit
        ref: "tests/test_scenarios.py#test_fallback_scenario_primary_fails_fallback_succeeds"
        status: pass
      - kind: unit
        ref: "tests/test_ui.py#test_run_fallback_inference_produces_fallback_succeeded_run"
        status: pass
      - kind: unit
        ref: "tests/test_ui.py#test_telemetry_rows_render_fallback_evidence"
        status: pass
    human_judgment: false
  - id: D3
    description: "Successful fallback does not hide the failed primary attempt in telemetry or history"
    requirement: ROUTE-06
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_telemetry_rows_render_fallback_evidence"
        status: pass
      - kind: unit
        ref: "tests/test_ui.py#test_run_fallback_inference_appends_to_history"
        status: pass
      - kind: unit
        ref: "tests/test_imports.py#test_live_boundaries_raise_honest_phase_errors"
        status: pass
    human_judgment: false

duration: 15 min
completed: 2026-08-19
status: complete
---

# Phase 3 Plan 02: Fallback Scenario Vertical Slice Summary

**Client-side two-attempt fallback orchestration with primary failure evidence preserved in the UI.**

## Performance

- **Duration:** 15 min
- **Tasks:** 3 completed
- **Files modified:** 4

## Accomplishments

- Implemented `run_fallback_scenario()` async generator with a deterministic primary failure (nonexistent model, `allow_fallbacks: false`) followed by a real fallback attempt.
- Added `_run_fallback_inference()` that builds `InferenceRun(status=FALLBACK_SUCCEEDED)` with `FallbackEvidence` preserving both attempts.
- Added a "Simulate primary route failure" toggle and wired telemetry panel to render primary status/error, fallback model/status, and failure type rows.
- Removed the `run_scenario` stub (kept `PhaseNotImplementedError`) and updated `test_imports.py` accordingly.

## Task Commits

1. **Task 1: Fallback scenario orchestration** - `726c243` (feat)
2. **Task 2: UI fallback handler, toggle, evidence rendering** - `2675d7a` (feat)
3. **Task 3: Full suite verification and ruff gate** - `9f551ba` (style)

## Files Created/Modified

- `src/openrouter_demo/scenarios.py` - run_fallback_scenario, FallbackResult, StreamFn alias
- `src/openrouter_demo/ui.py` - _run_fallback_inference, simulate_failure switch, fallback evidence rows
- `tests/test_scenarios.py` - fallback orchestration tests
- `tests/test_ui.py` - fallback inference and evidence rendering tests
- `tests/test_imports.py` - run_fallback_scenario importable assertion

## Decisions Made

- The fallback attempt does not catch `OpenRouterError` — if it fails, the exception propagates to the UI handler (which is responsible for surfacing final failure).
- `FallbackResult.fallback` is `StreamedResult | None`, where `None` only occurs when the primary unexpectedly succeeds (edge case treated as a normal run).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test data adjustment] Error message made consistent with real client output**
- **Found during:** Task 1 (fallback scenario orchestration)
- **Issue:** Plan's test dual-stream raised `OpenRouterHTTPError("Model not found", status_code=404)` but asserted `"404" in error_message`. `str(OpenRouterError)` returns only the message, so "404" was absent.
- **Fix:** Changed the injected error message to `"OpenRouter request failed (404)"`, matching what `client.py` actually produces.
- **Files modified:** `tests/test_scenarios.py`, `tests/test_ui.py`
- **Verification:** `uv run pytest tests/test_scenarios.py tests/test_ui.py -q` → 26 passed.

**2. [Rule 1 - Pre-existing issue] Unformatted files outside Phase 3 scope**
- **Found during:** Task 3 (full suite verification and ruff gate)
- **Issue:** `ruff format --check .` flags pre-existing formatting in `client.py`, `history.py`, `telemetry.py`, `test_config.py` — none touched by Phase 3.
- **Fix:** Left untouched (surgical changes rule). Formatted only Phase 3 files.
- **Verification:** Phase 3 files pass `ruff format --check`; `ruff check .` passes.

**Total deviations:** 2 auto-fixed. **Impact:** None on delivered scope.

## Self-Check: PASSED

- `uv run pytest tests/ -q` → 50 passed
- `uv run ruff check .` → All checks passed
- Phase 3 files pass `uv run ruff format --check`
