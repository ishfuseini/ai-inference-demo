---
phase: 3
slug: routing-and-fallback-demo
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-08-19
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (via `uv run pytest`) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/ -q` |
| **Full suite command** | `uv run pytest tests/ -v && uv run ruff check . && uv run ruff format --check .` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -q`
- **After every plan wave:** Run `uv run pytest tests/ -v && uv run ruff check . && uv run ruff format --check .`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | ROUTE-01 | T-03-02 | N/A | unit | `uv run pytest tests/test_routing.py -q` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | ROUTE-02 | — | N/A | unit | `uv run pytest tests/test_ui.py -q` | ✅ | ⬜ pending |
| 03-01-03 | 01 | 1 | ROUTE-03 | — | N/A | unit | `uv run pytest tests/test_ui.py -q` | ✅ | ⬜ pending |
| 03-02-01 | 02 | 2 | ROUTE-04 | T-03-05 | N/A | unit | `uv run pytest tests/test_scenarios.py -q` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 2 | ROUTE-05 | T-03-06 | N/A | unit | `uv run pytest tests/test_scenarios.py tests/test_ui.py -q` | ❌ W0 | ⬜ pending |
| 03-02-03 | 02 | 2 | ROUTE-06 | T-03-08 | N/A | unit | `uv run pytest tests/test_ui.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_routing.py` — TDD tracer task (03-01-01) creates test file with strategy payload assertions (ROUTE-01)
- [x] `tests/test_scenarios.py` — TDD tracer task (03-02-01) creates test file with fallback scenario assertions (ROUTE-04, ROUTE-05, ROUTE-06)
- [x] `tests/test_ui.py` — extended by Plan 01 Task 2 and Plan 02 Task 2 for strategy selector, fallback toggle, fallback display

*TDD tracer tasks handle test creation — no separate Wave 0 scaffold needed. Existing infrastructure covers pytest and ruff.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Strategy selector renders three options in browser | ROUTE-01 | Visual rendering in NiceGUI | Launch `uv run python app.py`, verify dropdown shows Default/Cost/Latency |
| Fallback success state shows both attempts in browser | ROUTE-05, ROUTE-06 | Visual rendering of fallback evidence | Launch app, toggle "Simulate primary route failure", run inference, verify both primary failure and fallback success visible |
| Strategy tradeoff text updates on selection | ROUTE-02 | Visual text update on UI interaction | Launch app, select each strategy, verify description text changes |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (TDD tracer tasks create test files)
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending