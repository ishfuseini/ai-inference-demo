---
phase: 03-routing-and-fallback-demo
type: verification
status: passed
created: 2026-08-19
---

# Phase 3 Verification: Routing and Fallback Demo

## Phase Goal

> User can compare strategy tradeoffs and trigger a fallback path that preserves primary failure evidence.

## Goal-Backward Analysis

Each success criterion traced to implementation and a passing test.

| # | Success Criterion | Implementation | Evidence |
|---|---|---|---|
| 1 | User can choose default, cost, and latency strategies before running | `STRATEGIES` dict + `strategy_select` ui.select in `ui.py` | `tests/test_routing.py::test_strategies_dict_contains_three_selectable_strategies` |
| 2 | UI explains each strategy in reviewer-facing tradeoff language | `RoutingStrategy.description` hardcoded from screen spec; `strategy_description_label` updates on selection | `tests/test_imports.py::test_routing_labels_do_not_claim_provider_results` (labels); descriptions verified against `docs/ux/screen-spec.md` |
| 3 | Completed runs show selected strategy and actual route/model evidence | `InferenceRun.strategy_name` + `TelemetryEvidence.model/provider`; `_telemetry_rows` renders Strategy/Model/Provider | `tests/test_ui.py::test_run_inference_records_cost_strategy_name`, `::test_run_inference_records_latency_strategy_name`, `::test_telemetry_rows_reflect_run_strategy` |
| 4 | Fallback shows primary attempt, failure reason, fallback route, final result | `run_fallback_scenario` two-attempt orchestration; `FallbackEvidence` on `InferenceRun`; `_telemetry_rows` renders Primary status/error, Fallback model/status | `tests/test_scenarios.py::test_fallback_scenario_primary_fails_fallback_succeeds`, `tests/test_ui.py::test_telemetry_rows_render_fallback_evidence` |
| 5 | Successful fallback never hides the failed primary attempt | `_run_fallback_inference` sets `status=FALLBACK_SUCCEEDED` and attaches `fallback_evidence`; telemetry renders both attempts; history shows "Yes" in Fallback column | `tests/test_ui.py::test_run_fallback_inference_produces_fallback_succeeded_run`, `::test_telemetry_rows_render_fallback_evidence`, `::test_history_rows_include_fallback_column` |

## Requirements Coverage

| ID | Status | Test |
|---|---|---|
| ROUTE-01 | pass | `tests/test_routing.py` (payload + STRATEGIES dict) |
| ROUTE-02 | pass | `tests/test_imports.py::test_routing_labels_do_not_claim_provider_results` + strategy descriptions |
| ROUTE-03 | pass | `tests/test_ui.py::test_run_inference_records_cost_strategy_name`, `::test_telemetry_rows_reflect_run_strategy` |
| ROUTE-04 | pass | `tests/test_scenarios.py::test_fallback_scenario_primary_fails_fallback_succeeds` |
| ROUTE-05 | pass | `tests/test_scenarios.py` + `tests/test_ui.py::test_telemetry_rows_render_fallback_evidence` |
| ROUTE-06 | pass | `tests/test_ui.py::test_run_fallback_inference_produces_fallback_succeeded_run` |

## Gate Results

- `uv run pytest tests/ -q` → **50 passed**
- `uv run ruff check .` → **All checks passed**
- Phase 3 files pass `uv run ruff format --check`

## Metadata Honesty Checks

- `UNAVAILABLE` sentinel remains distinct from zero for primary attempt tokens/cost/provider (`test_fallback_scenario_primary_fails_fallback_succeeds` asserts `primary.provider is UNAVAILABLE`).
- `ROUTING_STRATEGY_LABELS` unchanged (`test_imports.py` exact dict equality).
- `strategy_payload(DEFAULT_STRATEGY)` emits no `provider` key (`test_default_strategy_payload_has_no_provider`).

## Verdict

**Status: passed** — Phase 3 delivers all five success criteria with deterministic test evidence. No gaps found.

## Verification Complete
