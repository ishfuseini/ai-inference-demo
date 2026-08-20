---
phase: 04-telemetry-repeat-observability
plan: 02
subsystem: observability
tags: [openrouter, cache, repeat, telemetry, nicegui]

# Dependency graph
requires:
  - phase: 04-telemetry-repeat-observability
    plan: 01
    provides: StreamedResult/TelemetryEvidence cache fields, _extract_cache, record_trace
provides:
  - RepeatObservation dataclass + InferenceRun.repeat_observation field
  - run_repeat_scenario two-run orchestration with cache honesty
  - _run_repeat_inference + Repeat UI switch with cache-or-delta rendering
affects: [04-03, 05-deterministic-evals]

# Actuals
actuals:
  tokens: 28000
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-run injected-stream_fn scenario (mirrors run_fallback_scenario)"
    - "Cache status derives only from run 2's prompt_tokens_details; latency/cost delta is the fallback"

key-files:
  created:
    - tests/test_repeat.py
  modified:
    - src/openrouter_demo/models.py
    - src/openrouter_demo/scenarios.py
    - src/openrouter_demo/ui.py
    - tests/test_ui.py

key-decisions:
  - "run_repeat_scenario yields only run 2's StreamChunks; run 1 is observed silently."
  - "RepeatObservation.cache_* fields come from run 2's StreamedResult only — run 1 cache fields never contribute."
  - "When cache_status is UNAVAILABLE and repeat_observation is present, the Cache row renders the observed first→second latency/cost delta (OBS-04)."

patterns-established:
  - "Cache-or-delta rendering: _format_cache_cell(run) renders hit/write, observed repeat delta, or unavailable copy."

requirements-completed: [OBS-03, OBS-04]

# Coverage metadata
coverage:
  - id: D1
    description: "run_repeat_scenario two-run orchestration yielding a RepeatObservation with honest cache status derived only from run 2."
    requirement: OBS-03
    verification:
      - kind: unit
        ref: "tests/test_repeat.py#test_repeat_scenario_reports_cache_hit_from_run_2"
        status: pass
      - kind: unit
        ref: "tests/test_repeat.py#test_repeat_scenario_cache_derives_only_from_run_2"
        status: pass
      - kind: unit
        ref: "tests/test_repeat.py#test_repeat_scenario_reports_absent_cache_with_latency_and_cost"
        status: pass
    human_judgment: false
  - id: D2
    description: "Repeat UI action re-runs the last prompt and records a completed run whose Cache row shows provider cache metadata or the observed latency/cost delta."
    requirement: OBS-04
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_run_repeat_inference_produces_run_with_cache_and_delta"
        status: pass
      - kind: unit
        ref: "tests/test_ui.py#test_run_repeat_inference_records_cache_hit"
        status: pass
    human_judgment: false

# Metrics
duration: 15min
completed: 2026-08-19
status: complete
---

# Phase 4 Plan 02: Repeat/Cache Scenario Summary

**Repeat/cache scenario: two-run observation reports provider cache metadata only when present, otherwise observed first-vs-second latency and cost, with a Repeat UI action.**

## Performance

- **Duration:** 15 min
- **Tasks:** 2
- **Files modified:** 4 (1 created, 3 modified)

## Accomplishments

- `run_repeat_scenario` runs the same prompt/strategy twice and yields a `RepeatObservation` whose cache status derives only from run 2's `prompt_tokens_details`.
- `RepeatObservation` and `InferenceRun.repeat_observation` added without breaking existing constructors.
- `_run_repeat_inference` and a "Repeat previous prompt" switch wire the two-run repeat into the UI, with a Cache row that shows cache hit/write or the observed latency/cost delta.

## Task Commits

Each task was committed atomically:

1. **Task 1: Repeat/cache scenario** - `cee9da3` (feat)
2. **Task 2: Repeat UI action** - `b816a58` (feat)

## Files Created/Modified

- `src/openrouter_demo/models.py` - `RepeatObservation` + `InferenceRun.repeat_observation`
- `src/openrouter_demo/scenarios.py` - `run_repeat_scenario`
- `src/openrouter_demo/ui.py` - `_run_repeat_inference`, Repeat switch, cache-or-delta cell
- `tests/test_repeat.py` - cache-honesty assertions
- `tests/test_ui.py` - repeat-inference run tests

## Decisions Made

As listed in `key-decisions` frontmatter.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Wave 3 (plan 04-03) can fix the SQLite round-trip and extend history comparison on top of the `repeat_observation` field and cache/trace fields produced here.

---
*Phase: 04-telemetry-repeat-observability*
*Completed: 2026-08-19*
