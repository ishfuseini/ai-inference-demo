---
phase: 04-telemetry-repeat-observability
plan: 01
subsystem: observability
tags: [openrouter, cache, trace, langfuse, telemetry, nicegui]

# Dependency graph
requires:
  - phase: 03-routing-and-fallback-demo
    provides: streaming client, routing strategies, fallback scenario, telemetry panel
provides:
  - Normalized TelemetryEvidence with cache/trace/router fields + sentinel-safe to_dict/from_dict
  - StreamedResult cache/router fields and X-OpenRouter-Metadata opt-in header
  - _extract_cache pure predicate over usage.prompt_tokens_details
  - record_trace/TraceOutcome conditional Langfuse tracing (disabled/enabled/failed)
affects: [04-02, 04-03, 05-deterministic-evals]

# Actuals
actuals:
  tokens: 30000
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Frozen dataclass field extension with default sentinels (non-breaking)"
    - "Conditional optional side-effect (Langfuse) that never blocks the main path"
    - "Pure predicate over parsed payloads for cache detection"

key-files:
  created:
    - tests/test_telemetry.py
  modified:
    - src/openrouter_demo/models.py
    - src/openrouter_demo/client.py
    - src/openrouter_demo/telemetry.py
    - src/openrouter_demo/ui.py
    - tests/test_client.py
    - tests/test_ui.py
    - tests/test_phase1_guards.py

key-decisions:
  - "Cache hit/write is derived ONLY from usage.prompt_tokens_details.cached_tokens/cache_write_tokens, never from latency/cost or openrouter_metadata."
  - "Unavailable sentinels serialize to a sentinel string ('__unavailable__') and round-trip through TelemetryEvidence.to_dict/from_dict so they never become {'label': 'unavailable'}."
  - "record_trace constructs the Langfuse client only inside a config.langfuse_ready branch and wraps tracing in a broad try/except returning trace_status=failed on any error."
  - "Trace input is limited to {'prompt': prompt}; the OpenRouter API key is never passed to Langfuse."

patterns-established:
  - "Cache/trace/router telemetry rows appended to _telemetry_rows in all three UI states (running/idle/completed)."

requirements-completed: [OBS-01, OBS-02, OBS-05, OBS-06]

# Coverage metadata
coverage:
  - id: D1
    description: "Normalized telemetry fields: TelemetryEvidence/StreamedResult cache-trace-router extension, _extract_cache predicate, X-OpenRouter-Metadata header, cache/router propagation from stream to telemetry."
    requirement: OBS-01
    verification:
      - kind: unit
        ref: "tests/test_telemetry.py#test_telemetry_evidence_round_trip_preserves_sentinels"
        status: pass
      - kind: unit
        ref: "tests/test_client.py#test_stream_sends_metadata_header_and_extracts_cache_hit"
        status: pass
      - kind: unit
        ref: "tests/test_client.py#test_stream_missing_cache_details_is_unavailable"
        status: pass
    human_judgment: false
  - id: D2
    description: "Conditional Langfuse tracing via record_trace/TraceOutcome, wired into normal and fallback runs with an optional config param that skips tracing when absent."
    requirement: OBS-05
    verification:
      - kind: unit
        ref: "tests/test_telemetry.py#test_record_trace_disabled_without_credentials"
        status: pass
      - kind: unit
        ref: "tests/test_telemetry.py#test_record_trace_failed_with_unreachable_langfuse"
        status: pass
      - kind: unit
        ref: "tests/test_telemetry.py#test_run_inference_trace_input_contains_no_api_key"
        status: pass
      - kind: unit
        ref: "tests/test_phase1_guards.py#test_phase1_keeps_langfuse_tracing_isolated_to_telemetry"
        status: pass
    human_judgment: false
  - id: D3
    description: "Router, Cache, and Trace telemetry rows render in the telemetry panel across running, idle, and completed states."
    requirement: OBS-02
    verification:
      - kind: unit
        ref: "tests/test_telemetry.py#test_telemetry_rows_include_cache_and_trace"
        status: pass
    human_judgment: true
    rationale: "Completed-state rows are unit-tested; the running/idle placeholder rows share the same helper path but have no dedicated assertion."

# Metrics
duration: 20min
completed: 2026-08-19
status: complete
---

# Phase 4 Plan 01: Normalized Telemetry Summary

**Normalized telemetry end-to-end: one run records cache/trace/router fields from stream to telemetry panel, with conditional Langfuse tracing that never blocks inference.**

## Performance

- **Duration:** 20 min
- **Tasks:** 2
- **Files modified:** 7 (1 created, 6 modified)

## Accomplishments

- `TelemetryEvidence` extended with seven defaulted fields (`cache_status`, `cached_tokens`, `cache_write_tokens`, `trace_status`, `trace_id`, `trace_url`, `openrouter_metadata`) plus sentinel-safe `to_dict`/`from_dict`; `StreamedResult` gained four defaulted fields.
- `client.py` now sends `X-OpenRouter-Metadata: enabled`, extracts `prompt_tokens_details` cache data via the pure `_extract_cache` predicate, and propagates cache/router metadata into the final `StreamedResult`.
- `record_trace`/`TraceOutcome` in `telemetry.py` produce conditional Langfuse traces (disabled/enabled/failed) without ever raising or blocking inference; fallback runs are traced too.
- Router, Cache, and Trace rows render in the telemetry panel in all three UI states, with honest `Unavailable` handling.

## Task Commits

Each task was committed atomically:

1. **Task 1: Normalized telemetry end-to-end** - `62ed0f0` (feat)
2. **Task 2: Conditional Langfuse tracing** - `c375c91` (feat)

## Files Created/Modified

- `src/openrouter_demo/models.py` - TelemetryEvidence/StreamedResult field extension + to_dict/from_dict
- `src/openrouter_demo/client.py` - X-OpenRouter-Metadata header, `_extract_cache`, cache/router capture
- `src/openrouter_demo/telemetry.py` - `TraceOutcome` + `record_trace`
- `src/openrouter_demo/ui.py` - Router/Cache/Trace rows, cache pass-through, optional config param
- `tests/test_telemetry.py` - normalization, round-trip, trace-toggle tests
- `tests/test_client.py` - metadata header + cache extraction tests
- `tests/test_ui.py` - optional-config trace behavior tests
- `tests/test_phase1_guards.py` - Langfuse isolation guard

## Decisions Made

As listed in `key-decisions` frontmatter.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Wave 2 (plan 04-02) can build the repeat/cache scenario on top of the `StreamedResult`/`TelemetryEvidence` cache fields produced by this plan.

---
*Phase: 04-telemetry-repeat-observability*
*Completed: 2026-08-19*
