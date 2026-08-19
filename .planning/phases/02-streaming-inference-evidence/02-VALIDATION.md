---
phase: 02
slug: streaming-inference-evidence
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-19
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for streaming UI evidence.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_ui.py -q` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Run the focused command in the task `<verify>` block.
- **After every plan wave:** Run `uv run pytest` plus `uv run ruff check .`.
- **Before `/gsd-verify-work`:** Full suite and Ruff must be green.
- **Max feedback latency:** 10 seconds for focused tests, 30 seconds for full suite.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | INF-01, INF-02, INF-04 | T-02-01 | Tests use mocked streams, not live OpenRouter | unit | `uv run pytest tests/test_ui.py -q` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | INF-03, INF-05, INF-06 | T-02-02 | Unavailable metadata remains non-zero sentinel/copy | unit | `uv run pytest tests/test_ui.py tests/test_client.py -q` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | INF-01, INF-02 | T-02-03 | Missing API key blocks request and shows setup guidance | unit/smoke | `uv run pytest tests/test_ui.py tests/test_config.py -q` | ✅ | ⬜ pending |
| 02-02-02 | 02 | 2 | INF-03, INF-04, INF-05, INF-06 | T-02-04 | UI never fabricates model/provider/token/cost evidence | unit/smoke | `uv run pytest && uv run ruff check .` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_ui.py` — focused tests for UI state handler, success stream, missing metadata, and mid-stream failure.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live OpenRouter streaming in browser | INF-01, INF-02, INF-03, INF-04, INF-05, INF-06 | Requires a real API key and network/provider availability | Export `OPENROUTER_API_KEY`, run `uv run python app.py`, submit a short prompt, confirm progressive response text, telemetry update, unavailable metadata copy where applicable, and one run-history row. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter after validate-phase confirms coverage

**Approval:** pending
