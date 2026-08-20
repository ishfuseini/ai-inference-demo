---
gsd_state_version: 1.0
milestone: v1.0
current_phase: 5
current_phase_name: Deterministic Evals
status: ready
stopped_at: Phase 4 complete
last_updated: "2026-08-19"
state_head: c412024
progress:
  total_phases: 6
  completed_phases: 4
  total_plans: 11
  completed_plans: 10
milestone_name: milestone
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-08-19)

**Core value:** Make production inference behavior visible and defensible in a five-minute interview demo.
**Current focus:** Phase 4 complete. Next: Phase 5: Deterministic Evals.

## Current Position

**Phase:** 4 (Telemetry, Repeat, and Observability) — COMPLETE
**Plan:** 3 plans executed (.planning/phases/04-telemetry-repeat-observability/04-01, 04-02, 04-03)
**Status:** Complete
**Next:** Phase 5: Deterministic Evals

```text
Progress: [##########] 100%
```

## Performance Metrics

| Metric | Current |
|--------|---------|
| Phases complete | 4/6 |
| Requirements mapped | 39/39 |
| Requirements complete | 25/39 |
| Plans complete | 10 |

## Accumulated Context

### Decisions

- Use existing `docs/` and `data/` as seed project material.
- Use Vertical MVP phases so each phase produces demonstrable interview value.
- Keep OpenRouter integration direct and inspectable.
- Keep Langfuse optional.
- Use `uv`, Ruff, and pytest as the quality gate path.
- Use client-side two-attempt orchestration for the fallback demo (server-side `models` array hides primary failure).
- `FALLBACK_PRIMARY_STRATEGY` uses `name="custom"` and is excluded from the selectable `STRATEGIES` dict.
- `strategy_payload()` emits a `provider` key only when `provider_preferences` is set.
- Cache hit/write is derived ONLY from `usage.prompt_tokens_details.cached_tokens`/`cache_write_tokens`, never from latency/cost or `openrouter_metadata`.
- `Unavailable` sentinels serialize to `"__unavailable__"` (and `{"label": "unavailable"}` from `asdict`) and round-trip back to `UNAVAILABLE` through `TelemetryEvidence.to_dict`/`from_dict` and `sqlite_store` rebuild helpers.
- Langfuse tracing is constructed only inside a `config.langfuse_ready` branch; `record_trace` returns `disabled`/`enabled`/`failed` and never blocks inference.
- Persistence uses one nested JSON document in the existing `telemetry_json` column (no ALTER TABLE); `telemetry_schema.py` removed as the dead competing schema.

### Todos

- Plan Phase 5 deterministic evals.

### Blockers

(None)

## Session Continuity

**Last session:** 2026-08-19
**Stopped at:** Phase 4 complete
**Resume file:** .planning/ROADMAP.md

Phase 4 added normalized telemetry (cache/trace/router fields on `TelemetryEvidence`/`StreamedResult`), the `X-OpenRouter-Metadata` opt-in header, a pure `_extract_cache` predicate, conditional Langfuse tracing (`record_trace`/`TraceOutcome`), a repeat/cache scenario (`run_repeat_scenario`/`RepeatObservation`) with a Repeat UI action, and a fixed SQLite round-trip plus 10-column history comparison. Phase 5 can add deterministic evals on top.

---
*Last updated: 2026-08-19 after Phase 4 execution*
