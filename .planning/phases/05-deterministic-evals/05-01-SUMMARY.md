---
phase: 05-deterministic-evals
plan: 01
subsystem: evals
tags: [openrouter, evals, deterministic, pytest, cli]

requires:
  - phase: 04-telemetry-repeat-observability
    provides: "client.stream_chat_completion, routing.STRATEGIES, models.TelemetryEvidence (+ UNAVAILABLE sentinel), telemetry.record_trace"
provides:
  - "Run 3-5 checked-in deterministic eval cases against >=2 strategies or models with pass/fail + score reason + honest telemetry"
  - "Per-strategy comparison summary (text table + --json) over pass count, total cost, mean latency, trace state"
  - "CLI `PYTHONPATH=src uv run python -m openrouter_demo.evals` with exit codes 0/1/2 and --cases/--strategies/--models/--limit/--json"
affects: [Phase 6 (interview walkthrough + quality gates: DOC-05 eval scoring tests, DOC-06 pytest)]

actuals:
  tokens: 7200
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Deterministic keyword scoring (expected_terms all present / forbidden_terms none present) with no LLM judge"
    - "Async case runner composing stream_chat_completion -> record_trace -> TelemetryEvidence -> EvalResult"
    - "Injectable StreamFn for zero-network tests (mirrors tests/test_scenarios.py)"

key-files:
  created:
    - src/openrouter_demo/evals.py
    - evals/cases.json
    - tests/test_evals.py
  modified:
    - tests/test_imports.py
    - tests/test_phase1_guards.py

key-decisions:
  - "Deterministic v1 scores binary criteria only via keyword matching; tone score/composite deferred to V2-01 LLM-as-judge"
  - "cases.json is the checked-in eval source (5 cases derived from data/api-complaint.csv); data/*.csv stays read-only seed"
  - "Comparison defaults to strategies default,cost; --models switches to model-id grouping via the existing model= override (routing.STRATEGIES unchanged)"
  - "Exit codes: 0 = ran (pass/fail is data), 1 = config error, 2 = runtime error"

patterns-established:
  - "Pure score_response(case, text) predicate — testable with zero network"
  - "main() reads api_key from os.environ once and never passes it into record_trace/format_summary"

requirements-completed: [EVAL-01, EVAL-02, EVAL-03, EVAL-04, EVAL-05, EVAL-06]

coverage:
  - id: D1
    description: "Deterministic eval CLI (evals.py) implementing EvalCase/EvalResult/EvalSummary, score_response, run_eval_case, run_eval_set, load_cases, format_summary, build_parser, main"
    requirement: EVAL-01
    verification:
      - kind: unit
        ref: "tests/test_evals.py#test_run_eval_case_result_fields"
        status: pass
      - kind: unit
        ref: "tests/test_evals.py#test_run_eval_case_preserves_unavailable"
        status: pass
    human_judgment: false
  - id: D2
    description: "5 checked-in deterministic cases in evals/cases.json with a 3-5 count gate in load_cases"
    requirement: EVAL-01
    verification:
      - kind: unit
        ref: "tests/test_evals.py#test_load_cases_reads_five_cases"
        status: pass
      - kind: unit
        ref: "tests/test_evals.py#test_load_cases_rejects_out_of_bounds"
        status: pass
    human_judgment: false
  - id: D3
    description: "Deterministic scoring (score_response) and honest telemetry (UNAVAILABLE preservation + trace disabled/enabled + no API key in trace input)"
    requirement: EVAL-02
    verification:
      - kind: unit
        ref: "tests/test_evals.py#test_score_response_passes_and_fails"
        status: pass
      - kind: unit
        ref: "tests/test_evals.py#test_run_eval_case_trace_disabled_and_enabled"
        status: pass
      - kind: unit
        ref: "tests/test_evals.py#test_run_eval_case_trace_input_has_no_api_key"
        status: pass
    human_judgment: false
  - id: D4
    description: "Per-strategy comparison summary (text + --json) across >=2 strategies or models"
    requirement: EVAL-06
    verification:
      - kind: unit
        ref: "tests/test_evals.py#test_format_summary_json_is_parseable"
        status: pass
      - kind: unit
        ref: "tests/test_evals.py#test_run_eval_set_uses_models_override"
        status: pass
    human_judgment: false
  - id: D5
    description: "CLI exit-code contract (0/1/2) and --models/--limit/--json edge behavior"
    requirement: EVAL-01
    verification:
      - kind: unit
        ref: "tests/test_evals.py#test_main_missing_api_key_exits_nonzero"
        status: pass
      - kind: unit
        ref: "tests/test_evals.py#test_main_exits_1_on_unreadable_cases"
        status: pass
      - kind: unit
        ref: "tests/test_evals.py#test_main_exits_2_on_runtime_error"
        status: pass
      - kind: unit
        ref: "tests/test_evals.py#test_main_limit_caps_cases"
        status: pass
    human_judgment: false
  - id: D6
    description: "Live eval run against real OpenRouter (3-5 cases, per-strategy pass/latency/cost/trace) with OPENROUTER_API_KEY"
    verification: []
    human_judgment: true
    rationale: "Requires a real OPENROUTER_API_KEY and live network; latency/tokens/cost/trace depend on the live route and cannot be asserted against a mock."

duration: 15min
completed: 2026-08-20
status: complete
---

# Phase 5: Deterministic Evals Summary

**Delivered a runnable deterministic eval CLI that executes 5 checked-in cases against two routing strategies and reports pass/fail with a score reason plus honest latency/token/cost/trace telemetry, by composing the existing stream/trace/telemetry path rather than building a new one.**

## Performance

- **Duration:** 15 min
- **Tasks:** 3 completed
- **Files modified:** 5 (3 created, 2 modified)
- **Full suite:** `uv run pytest` — 98 passed

## Accomplishments

- Replaced the `evals.py` Phase 5 stub with a full module: `EvalCase`/`EvalResult`/`EvalSummary` dataclasses, pure `score_response`, async `run_eval_case`/`run_eval_set`, `load_cases`, `format_summary`, and an argparse `main()`.
- Added 5 deterministic cases in `evals/cases.json` (derived from `data/api-complaint.csv`), scored by keyword matching with no LLM judge.
- Wired the eval runner through the existing `stream_chat_completion` → `record_trace` → `TelemetryEvidence` path, preserving the `UNAVAILABLE` sentinel and never leaking the API key into traces or output.
- Delivered a per-strategy comparison summary (text table and `--json`) with pass count, total cost, mean latency, and trace state.
- Updated the two Phase 1/4 placeholder guard tests in the same wave so `uv run pytest` stays green.

## Task Commits

Each task was committed atomically:

1. **Task 1 (tracer): end-to-end eval CLI** - `9d9bc9e` (feat)
2. **Task 2: expand to 5 canonical cases + comparison summary tests** - `4cf6fff` (feat)
3. **Task 3: CLI exit-code contract + edge coverage tests** - `aade335` (feat)

## Files Created/Modified

- `src/openrouter_demo/evals.py` — the deterministic eval module (created; replaced stub)
- `evals/cases.json` — 5 checked-in deterministic cases (created)
- `tests/test_evals.py` — 20 zero-network tests covering EVAL-01..06 + exit-code hygiene (created)
- `tests/test_imports.py` — two Phase 1 placeholder guards rewritten for the implemented module (modified)
- `tests/test_phase1_guards.py` — `evals.py` added to the Langfuse-isolation `core_modules` list (modified)

## Decisions Made

- Deterministic v1 scores binary criteria only (keyword matching); tone score/composite deferred to V2-01.
- `cases.json` is the checked-in eval source; `data/*.csv` and the rubric stay read-only seed material.
- `--strategies default,cost` is the default comparison; `--models` switches to model-id grouping with no change to `routing.STRATEGIES`.
- Exit codes: 0 = ran, 1 = config error, 2 = runtime error.

## Deviations from Plan

- **Rule 1 (bug/robustness) — `test_load_cases_reads_three_to_five_cases`** — wrote the assertion as `3 <= len(cases) <= 5` (matching the test name and the load_cases 3–5 gate) rather than the plan's literal `len == 3`, so the test stays green after Task 2 expands `cases.json` to 5 cases. Auto-fixed during Task 1.
- **Rule 1 (bug) — `main()` passes `config=` and `stream_fn=` explicitly** to `run_eval_set` (the plan's abbreviated action omitted them, but both are required by the signatures and `stream_fn=` must be a call-time module-global lookup so tests can monkeypatch `stream_chat_completion`). Auto-fixed during Task 1.
- **Rule 1 (lint) — Ruff fixes** — removed the unused `UNAVAILABLE` import and `int | float` redundant unions, and prefixed an unused unpacked `reason` variable in a test. Auto-fixed during Task 3.

**Total deviations:** 3 auto-fixed (2 correctness/robustness, 1 lint). **Impact:** none on scope — all acceptance criteria and the plan's `must_haves` hold.

## Self-Check: PASSED
