---
phase: 5
slug: deterministic-evals
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-19
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ≥9.1.1 (via `uv run pytest`) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` — `testpaths = ["tests"]`, `pythonpath = ["src"]` |
| **Quick run command** | `uv run pytest tests/test_evals.py -q` |
| **Full suite command** | `uv run pytest && uv run ruff check .` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_evals.py -q`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | EVAL-01/EVAL-02 | T-05-01 / — | `load_cases` returns 3–5 cases; `score_response` is pure + deterministic; model text treated as data, never `eval`/`exec` | unit | `uv run pytest tests/test_evals.py -q` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | EVAL-03/EVAL-04 | T-05-02 / — | `EvalResult` carries `strategy_name`/`passed`/`score_reason`; `TelemetryEvidence` preserves `UNAVAILABLE` (never coerced to 0) | unit | `uv run pytest tests/test_evals.py -q` | ❌ W0 | ⬜ pending |
| 05-01-03 | 01 | 1 | EVAL-05 | T-05-03 / — | `trace_status="disabled"` without Langfuse; `"enabled"` + `trace_id` with mocked `record_trace`; trace input never contains `api_key` | unit | `uv run pytest tests/test_evals.py -q` | ❌ W0 | ⬜ pending |
| 05-01-04 | 01 | 1 | EVAL-06 | T-05-04 / — | `run_eval_set` executes ≥2 strategies; `EvalSummary` groups per strategy | unit | `uv run pytest tests/test_evals.py -q` | ❌ W0 | ⬜ pending |
| 05-01-05 | 01 | 1 | — (CLI hygiene) | T-05-04 / — | `main()` exits `1` with missing `OPENROUTER_API_KEY` and never calls the network | unit | `uv run pytest tests/test_evals.py -q` | ❌ W0 | ⬜ pending |
| 05-01-06 | 01 | 1 | — (guard update) | T-05-SC / — | `test_imports.py` Phase-1 placeholder guards updated to reflect implemented evals + `cases.json` | unit | `uv run pytest tests/test_imports.py tests/test_phase1_guards.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_evals.py` — new file covering EVAL-01..06 (load_cases, score_response, run_eval_case fields, UNAVAILABLE preservation, trace disabled/enabled, multi-strategy summary, missing-key exit)
- [ ] Update `tests/test_imports.py` — rewrite `test_live_boundaries_raise_honest_phase_errors` (evals no longer raises `PhaseNotImplementedError`) and `test_evals_directory_has_no_phase1_cases` (`evals/cases.json` now exists)
- [ ] Verify `tests/test_phase1_guards.py` still passes — `evals.py` must not import forbidden modules, tracing must go through `telemetry.record_trace`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live eval run against a real provider | EVAL-01/EVAL-04 | Requires `OPENROUTER_API_KEY`; latency/tokens/cost depend on the live route | `PYTHONPATH=src uv run python -m openrouter_demo.evals` with the key exported; confirm 3–5 cases run and summary shows per-strategy pass/latency/cost |
| Langfuse trace visible in Langfuse UI | EVAL-05 | Requires live `LANGFUSE_*` credentials and a real trace round-trip | Run the eval set with Langfuse configured; confirm trace IDs render; unset credentials and confirm `trace disabled` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
