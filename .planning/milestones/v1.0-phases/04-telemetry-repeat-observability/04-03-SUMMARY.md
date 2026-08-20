---
phase: 04-telemetry-repeat-observability
plan: 03
subsystem: persistence
tags: [sqlite, telemetry, history, comparison, nicegui]

# Dependency graph
requires:
  - phase: 04-telemetry-repeat-observability
    plan: 02
    provides: RepeatObservation + InferenceRun.repeat_observation + cache/trace fields
provides:
  - SQLiteRunHistory nested-document round-trip preserving Unavailable sentinels, cache/trace, fallback/repeat evidence
  - 10-column history grid with Cache and Trace columns + comparison section
  - Removed dead telemetry_schema.py (single schema of truth)
affects: [05-deterministic-evals]

# Actuals
actuals:
  tokens: 26000
  tasks: 3
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single nested JSON document in telemetry_json column (no schema migration)"
    - "Legacy flat-row compatibility branch in _row_to_run"

key-files:
  created:
    - tests/test_sqlite_store.py
  modified:
    - src/openrouter_demo/sqlite_store.py
    - src/openrouter_demo/ui.py
    - tests/test_ui.py
    - tests/test_imports.py
  deleted:
    - src/openrouter_demo/telemetry_schema.py

key-decisions:
  - "Persistence uses one nested JSON document {'telemetry': ..., 'fallback_evidence': ..., 'repeat_observation': ...} in the existing telemetry_json column; no ALTER TABLE."
  - "TelemetryEvidence round-trips via to_dict/from_dict with a '__unavailable__' sentinel; asdict-serialized fallback/repeat evidence is rebuilt field-by-field with {'label': 'unavailable'} mapped back to UNAVAILABLE."
  - "Legacy flat-format rows load through a compatibility branch (fallback_evidence=None) rather than raising."
  - "Removed the obsolete telemetry_schema.py so models.TelemetryEvidence is the single schema of truth."

patterns-established:
  - "10-column history grid + 6-column comparison section reuse the _format_* helpers and never stringify UNAVAILABLE directly."

requirements-completed: [OBS-07]

# Coverage metadata
coverage:
  - id: D1
    description: "SQLite persistence round-trip preserves Unavailable sentinels, cache/trace fields, and fallback/repeat evidence across save/load."
    requirement: OBS-07
    verification:
      - kind: unit
        ref: "tests/test_sqlite_store.py#test_round_trip_preserves_sentinels_cache_trace_and_fallback"
        status: pass
      - kind: unit
        ref: "tests/test_sqlite_store.py#test_round_trip_preserves_unavailable_cache_status"
        status: pass
      - kind: unit
        ref: "tests/test_sqlite_store.py#test_legacy_flat_row_loads_via_compatibility_branch"
        status: pass
    human_judgment: false
  - id: D2
    description: "10-column run history with Cache/Trace columns and a comparison view of recent completed runs in the main UI."
    requirement: OBS-07
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_history_rows_render_cache_and_trace_columns"
        status: pass
      - kind: unit
        ref: "tests/test_ui.py#test_comparison_rows_include_completed_runs"
        status: pass
      - kind: unit
        ref: "tests/test_imports.py#test_phase4_types_and_fields_importable"
        status: pass
    human_judgment: true
    rationale: "The comparison grid rendering (NiceGUI labels) is exercised via _comparison_rows data; visual layout in the browser is not screenshot-tested."
  - id: D3
    description: "Removed the orphaned telemetry_schema.py so the repo has one telemetry schema."
    requirement: OBS-07
    verification:
      - kind: unit
        ref: "tests/test_imports.py#test_phase4_types_and_fields_importable"
        status: pass
      - kind: other
        ref: "grep -rn telemetry_schema src/ tests/ (empty) and grep -rn RunRecord|FallbackAttempt src/ tests/ (empty)"
        status: pass
    human_judgment: false

# Metrics
duration: 20min
completed: 2026-08-19
status: complete
---

# Phase 4 Plan 03: Persistence and Comparison Summary

**Persistence round-trip preserves Unavailable sentinels, cache/trace fields, and fallback/repeat evidence; the history UI gains Cache/Trace columns and a comparison view; the dead telemetry schema is removed.**

## Performance

- **Duration:** 20 min
- **Tasks:** 3
- **Files modified:** 5 (1 created, 3 modified, 1 deleted)

## Accomplishments

- `SQLiteRunHistory` now stores a single nested JSON document and rebuilds `TelemetryEvidence` via `from_dict`, preserving sentinels and cache/trace/fallback/repeat data; legacy flat rows load through a compatibility branch.
- `_history_rows` extended to 10 columns (Cache + Trace); a comparison section of recent completed runs (Model/Provider/Latency/Cost/Cache/Trace) renders below the history grid.
- Removed the obsolete `telemetry_schema.py` so `models.TelemetryEvidence` is the single schema of truth.

## Task Commits

Each task was committed atomically:

1. **Task 1: Persistence round-trip** - `38ac410` (feat)
2. **Task 2: History comparison** - `a274062` (feat)
3. **Task 3: Remove dead telemetry_schema.py** - `e93a88b` (refactor)

## Files Created/Modified

- `src/openrouter_demo/sqlite_store.py` - nested-document round-trip + legacy compat
- `src/openrouter_demo/ui.py` - 10-column history + comparison section; removed "Future operation panels"
- `tests/test_sqlite_store.py` - round-trip sentinel/fallback tests
- `tests/test_ui.py` - 10-column and comparison assertions
- `tests/test_imports.py` - Phase 4 type/field import assertions
- `src/openrouter_demo/telemetry_schema.py` - deleted

## Decisions Made

As listed in `key-decisions` frontmatter.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 4 is complete. Phase 5 (Deterministic Evals) can build on the normalized telemetry, repeat observation, and comparison history produced here.

---
*Phase: 04-telemetry-repeat-observability*
*Completed: 2026-08-19*
