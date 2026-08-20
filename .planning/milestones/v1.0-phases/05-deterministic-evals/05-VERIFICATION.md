---
phase: 05-deterministic-evals
verified: 2026-08-20T06:30:00Z
status: passed
score: 6/6 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 5/6
  gaps_closed:
    - "PYTHONPATH=src uv run python -m openrouter_demo.evals (with OPENROUTER_API_KEY exported) runs 3-5 deterministic cases, prints a summary comparing >=2 strategies or models, and exits 0."
  gaps_remaining: []
  regressions: []
---

# Phase 5: Deterministic Evals Verification Report (Re-verification)

**Phase Goal:** User can run three to five deterministic eval cases and compare quality, latency, cost, model/provider, and trace state.
**Verified:** 2026-08-20T06:30:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure

## Verdict Summary

The single BLOCKER from the initial verification is closed. `src/openrouter_demo/evals.py` now ends with `if __name__ == "__main__": sys.exit(main())`, so `python -m openrouter_demo.evals` actually runs `main()` instead of importing silently and exiting 0. Two new regression tests pin this behavior: `test_evals_has_module_entry_point` (asserts the guard is present in source) and `test_python_m_evals_exits_1_without_api_key` (subprocess: asserts exit 1 plus the missing-key error). Full suite is now 100 passed, `ruff check .` is clean, and the CLI empirically prints `OPENROUTER_API_KEY is not set. Export it and retry.` and exits 1 when the key is unset.

## Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `python -m openrouter_demo.evals` runs 3-5 cases, prints a comparison summary, exits 0 | ✓ VERIFIED | `evals.py` ends with `if __name__ == "__main__": sys.exit(main())`. Empirical: `env -u OPENROUTER_API_KEY PYTHONPATH=src uv run python -m openrouter_demo.evals` → `OPENROUTER_API_KEY is not set. Export it and retry.` + exit 1. `test_evals_has_module_entry_point` + `test_python_m_evals_exits_1_without_api_key` pass; `test_main_runs_end_to_end_with_fake_stream` proves exit 0 + summary on a successful run. |
| 2 | Every `EvalResult` carries strategy_name/passed/score_reason; telemetry carries model/provider/latency/tokens/cost/trace with UNAVAILABLE preserved | ✓ VERIFIED | `EvalResult`/`TelemetryEvidence` assembly in `run_eval_case`; `test_run_eval_case_result_fields`, `test_run_eval_case_preserves_unavailable` pass. |
| 3 | `score_response` pure + deterministic (case-insensitive substring; pass iff all expected present, no forbidden present) | ✓ VERIFIED | `.lower() in` only, no eval/exec; `test_score_response_passes_and_fails` passes. |
| 4 | `trace_status` disabled/enabled/failed; trace input is `{"prompt": ...}` only, never the API key | ✓ VERIFIED | `record_trace(input={"prompt": case.prompt}, ...)`; `test_run_eval_case_trace_disabled_and_enabled` + `test_run_eval_case_trace_input_has_no_api_key` pass. |
| 5 | `EvalSummary` groups by strategy/model; per-strategy pass count, total cost, mean latency, trace state across >=2 | ✓ VERIFIED | `EvalSummary.by_strategy` + `_aggregate` + `format_summary`; `test_format_summary_json_is_parseable` asserts 2 strategies / 10 results. |
| 6 | `main()` returns 1 on missing key/unreadable cases/unknown strategy, 2 on runtime error | ✓ VERIFIED | `test_main_missing_api_key_exits_nonzero`, `test_main_exits_1_on_unreadable_cases`, `test_main_exits_1_on_unknown_strategy`, `test_main_exits_2_on_runtime_error` pass. |

**Score:** 6/6 truths verified (0 present, behavior-unverified).

## Requirement Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| EVAL-01 | Eval command runs 3–5 deterministic cases | ✓ VERIFIED | `load_cases` enforces 3–5; `__main__` guard added; CLI runnable via `python -m openrouter_demo.evals`. |
| EVAL-02 | Each case has a clear pass/fail rule | ✓ VERIFIED | `score_response`; `test_score_response_passes_and_fails`. |
| EVAL-03 | Output includes model/strategy, pass/fail, score reason | ✓ VERIFIED | `EvalResult.strategy_name/passed/score_reason`; `test_run_eval_case_result_fields`. |
| EVAL-04 | Output includes latency and token/cost when available | ✓ VERIFIED | Telemetry passthrough + UNAVAILABLE preserved; `test_run_eval_case_preserves_unavailable`. |
| EVAL-05 | Output includes trace IDs or disabled state | ✓ VERIFIED | `test_run_eval_case_trace_disabled_and_enabled`. |
| EVAL-06 | Summary compares >=2 strategies or models | ✓ VERIFIED | `test_run_eval_set_compares_two_strategies`, `test_run_eval_set_uses_models_override`, `test_format_summary_json_is_parseable`. |

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/openrouter_demo/evals.py` | EvalCase/EvalResult/EvalSummary + score_response/run_eval_case/run_eval_set/load_cases/format_summary/build_parser/main + `__main__` guard | ✓ VERIFIED | All symbols present and substantive; `if __name__ == "__main__": sys.exit(main())` at end of file. |
| `evals/cases.json` | 5 canonical cases | ✓ VERIFIED | 5 cases in declared order; `test_load_cases_reads_five_cases` passes. |
| `tests/test_evals.py` | 22 zero-network tests | ✓ VERIFIED | 22 tests including the 2 new entry-point tests, all green. |
| `tests/test_imports.py` | placeholder guards rewritten | ✓ VERIFIED | `test_evals_cases_json_has_three_to_five_cases` + `callable(evals_main)`. |
| `tests/test_phase1_guards.py` | `evals.py` in Langfuse-isolation `core_modules` | ✓ VERIFIED | `src/openrouter_demo/evals.py` in the list. |

## Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `main` → `load_cases` → `run_eval_set` → `run_eval_case` → `stream_chat_completion` → `score_response` + `record_trace` → `TelemetryEvidence` → `EvalResult` → `EvalSummary` → `format_summary` → stdout | — | async call chain | ✓ WIRED |
| `record_trace(config.langfuse_ready)` → `TelemetryEvidence.trace_status/trace_id/trace_url` | — | outcome passthrough | ✓ WIRED |
| command line → `main()` | — | `if __name__ == "__main__": sys.exit(main())` | ✓ WIRED (fixed) |

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite | `uv run pytest -q` | `100 passed in 3.90s` | ✓ PASS |
| Lint | `uv run ruff check .` | `All checks passed!` | ✓ PASS |
| CLI missing key | `env -u OPENROUTER_API_KEY PYTHONPATH=src uv run python -m openrouter_demo.evals; echo exit=$?` | `OPENROUTER_API_KEY is not set. Export it and retry.` + `exit=1` | ✓ PASS |

## Anti-Patterns Found

None. No `TBD`/`FIXME`/`XXX` debt markers, no empty implementations, no hardcoded-empty props, no stubs in the files modified by this phase.

## Human Verification

The following item requires live OpenRouter credentials and is **not a blocker** for automated verification — it is a demo-time check only. All six must-have truths and all six requirements (EVAL-01..06) are verified programmatically.

### 1. Live eval run against OpenRouter (needs credentials)

**Test:** With `OPENROUTER_API_KEY` exported, run `PYTHONPATH=src uv run python -m openrouter_demo.evals` and confirm 5 cases run against `default,cost`.
**Expected:** A summary with 10 results (5 × 2 strategies) and exit 0; with Langfuse configured trace IDs render, with Langfuse unset the summary shows trace disabled.
**Why human:** Requires a live API key and network; latency/tokens/cost/trace are route-dependent.

## Gaps Summary

None. The single blocker from the initial verification (missing `__main__` entry point) is fixed and pinned by two regression tests. All six must-have truths and all six requirements verify clean.

---

_Verified: 2026-08-20T06:30:00Z_
_Verifier: the agent (gsd-verifier)_
