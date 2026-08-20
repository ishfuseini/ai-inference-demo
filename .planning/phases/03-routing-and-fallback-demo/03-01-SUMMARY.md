---
phase: 03-routing-and-fallback-demo
plan: 01
subsystem: api
tags: [routing, strategy, provider-preferences, openrouter, nicegui]

requires:
  - phase: 02-streaming-inference-evidence
    provides: streaming inference console, InferenceRun model, stream_chat_completion
provides:
  - strategy registry (COST_STRATEGY, LATENCY_STRATEGY, FALLBACK_PRIMARY_STRATEGY)
  - STRATEGIES dict and provider-aware strategy_payload()
  - AttemptRecord and FallbackEvidence model types
  - Status.FALLBACK_SUCCEEDED enum value
  - InferenceRun.fallback_evidence field
  - UI strategy selector and description label
  - history Fallback column and fallback status copy
affects:
  - 03-02-PLAN.md (fallback scenario uses AttemptRecord/FallbackEvidence/FALLBACK_PRIMARY_STRATEGY)

actuals:
  tokens: 4200
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Strategy as inspectable policy object: RoutingStrategy instances carry provider_preferences emitted by strategy_payload()"
    - "Sentinel honesty: UNAVAILABLE stays distinct from zero for provider/model/tokens/cost metadata"

key-files:
  created:
    - tests/test_routing.py
  modified:
    - src/openrouter_demo/routing.py
    - src/openrouter_demo/models.py
    - src/openrouter_demo/ui.py
    - tests/test_ui.py
    - tests/test_imports.py

key-decisions:
  - "FALLBACK_PRIMARY_STRATEGY uses name='custom' and is excluded from STRATEGIES (not user-selectable)"
  - "strategy_payload() adds provider key only when provider_preferences is not None"
  - "ROUTING_STRATEGY_LABELS unchanged to preserve existing test_imports.py dict equality"

patterns-established:
  - "Strategy registry: STRATEGIES maps StrategyName to RoutingStrategy instances"
  - "Provider preferences flow: strategy_payload() -> client.py request body -> OpenRouter"

requirements-completed:
  - ROUTE-01
  - ROUTE-02
  - ROUTE-03

coverage:
  - id: D1
    description: "Strategy registry with provider preferences and selectable strategies"
    requirement: ROUTE-01
    verification:
      - kind: unit
        ref: "tests/test_routing.py#test_default_strategy_payload_has_no_provider"
        status: pass
      - kind: unit
        ref: "tests/test_routing.py#test_cost_strategy_payload_includes_price_sort"
        status: pass
      - kind: unit
        ref: "tests/test_routing.py#test_latency_strategy_payload_includes_latency_sort"
        status: pass
      - kind: unit
        ref: "tests/test_routing.py#test_strategies_dict_contains_three_selectable_strategies"
        status: pass
    human_judgment: false
  - id: D2
    description: "UI strategy selector with tradeoff description and strategy name recorded on run"
    requirement: ROUTE-02
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_run_inference_records_cost_strategy_name"
        status: pass
      - kind: unit
        ref: "tests/test_ui.py#test_run_inference_records_latency_strategy_name"
        status: pass
      - kind: unit
        ref: "tests/test_ui.py#test_strategies_dict_contains_three_selectable_strategies"
        status: pass
    human_judgment: false
  - id: D3
    description: "Completed run shows selected strategy and Fallback column in history"
    requirement: ROUTE-03
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_history_rows_include_fallback_column"
        status: pass
      - kind: unit
        ref: "tests/test_ui.py#test_telemetry_rows_fallback_success_status"
        status: pass
      - kind: unit
        ref: "tests/test_imports.py#test_phase3_types_importable"
        status: pass
    human_judgment: false

duration: 12 min
completed: 2026-08-19
status: complete
---

# Phase 3 Plan 01: Strategy Selection Vertical Slice Summary

**Strategy registry, provider-aware payloads, and model types wired into the UI selector end-to-end.**

## Performance

- **Duration:** 12 min
- **Tasks:** 3 completed
- **Files modified:** 6

## Accomplishments

- Added `COST_STRATEGY`, `LATENCY_STRATEGY`, `FALLBACK_PRIMARY_STRATEGY` and a `STRATEGIES` dict; `strategy_payload()` now emits the `provider` key when preferences exist.
- Added `AttemptRecord`, `FallbackEvidence`, `Status.FALLBACK_SUCCEEDED`, and the `InferenceRun.fallback_evidence` field to the model layer.
- Replaced the hardcoded "Default" label with a `ui.select` bound to the strategy registry, with a description label that updates on selection.
- Added a "Fallback" column to run history and fallback success copy to telemetry.

## Task Commits

1. **Task 1: Strategy registry, model types, and payload** - `a1ffba3` (feat)
2. **Task 2: UI strategy selector and description** - `26b430c` (feat)
3. **Task 3: Full suite verification and ruff gate** - `a4db4f3` (style)

## Files Created/Modified

- `src/openrouter_demo/routing.py` - strategy instances, STRATEGIES dict, provider-aware payload
- `src/openrouter_demo/models.py` - FALLBACK_SUCCEEDED, AttemptRecord, FallbackEvidence, fallback_evidence field
- `src/openrouter_demo/ui.py` - strategy selector, description label, Fallback history column, fallback status copy
- `tests/test_routing.py` - strategy payload and type tests
- `tests/test_ui.py` - strategy name, fallback column, fallback status tests
- `tests/test_imports.py` - test_phase3_types_importable

## Decisions Made

- `FALLBACK_PRIMARY_STRATEGY` uses `name="custom"` and is excluded from the selectable `STRATEGIES` dict.
- `AttemptRecord` and `FallbackEvidence` pre-import in `ui.py` was deferred to Plan 02 because ruff F401 rejects unused imports — Plan 02 imports them when actually used.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Scope adjustment] Deferred pre-imports to Plan 02**
- **Found during:** Task 2 (UI strategy selector and description)
- **Issue:** Plan instructed pre-importing `AttemptRecord`/`FallbackEvidence` in `ui.py` for Plan 02, but ruff F401 flags unused imports and Task 3 requires ruff to pass.
- **Fix:** Removed the pre-imports; Plan 02 will import them when actually used.
- **Files modified:** `src/openrouter_demo/ui.py`
- **Verification:** `uv run ruff check .` passes; full suite 43 passed.

**2. [Rule 1 - Pre-existing issue] Unformatted files outside Phase 3 scope**
- **Found during:** Task 3 (full suite verification and ruff gate)
- **Issue:** `ruff format --check .` flags pre-existing formatting in `history.py`, `scenarios.py`, `telemetry.py`, `test_config.py`, and planning markdown — none touched by Phase 3.
- **Fix:** Left untouched (surgical changes rule). Formatted only Phase 3 files.
- **Verification:** Phase 3 files pass `ruff format --check`; `ruff check .` passes.

**Total deviations:** 2 auto-fixed. **Impact:** None on delivered scope.

## Self-Check: PASSED

- `uv run pytest tests/ -q` → 43 passed
- `uv run ruff check .` → All checks passed
- Phase 3 files pass `uv run ruff format --check`
