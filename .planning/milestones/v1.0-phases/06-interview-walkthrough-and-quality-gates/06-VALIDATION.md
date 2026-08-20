---
phase: 6
slug: interview-walkthrough-and-quality-gates
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-20
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=9.1.1 (`[VERIFIED: pyproject.toml:14]`) |
| **Config file** | `pyproject.toml:21-23` — `testpaths = ["tests"]`, `pythonpath = ["src"]` |
| **Quick run command** | `uv run pytest -q` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~5 seconds (100 tests observed) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest -q`
- **After every plan wave:** Run `uv run pytest && uv run ruff check .`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | DOC-01 | T-06-01 / secret leak | README explains story/setup/env/walkthrough, no real keys | doc assertion | `uv run pytest tests/test_docs.py -q` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | DOC-02 | T-06-01 / secret leak | architecture guide covers routing/fallback/latency/cost/telemetry/eval flow | doc assertion | `uv run pytest tests/test_docs.py -q` | ❌ W0 | ⬜ pending |
| 06-01-03 | 01 | 1 | DOC-03 | T-06-01 / secret leak | failure tree covers client/credential/request/provider/routing/timeout/telemetry/display | doc assertion | `uv run pytest tests/test_docs.py -q` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 1 | DOC-04 | T-06-04 / availability | UI uses inference framing, no chatbot labels | unit | `uv run pytest tests/test_ui.py -q` | ✅ | ⬜ pending |
| 06-02-02 | 02 | 1 | DOC-05 | T-06-02 / spend | response/error, routing config, telemetry normalization, eval scoring covered | unit | `uv run pytest -q` | ✅ | ⬜ pending |
| 06-03-01 | 03 | 1 | DOC-06 | — | `uv run pytest` passes | gate | `uv run pytest` | ✅ (100 passed) | ⬜ pending |
| 06-03-02 | 03 | 1 | DOC-07 | — | `uv run ruff check .` passes | gate | `uv run ruff check .` | ✅ (clean) | ⬜ pending |
| 06-03-03 | 03 | 1 | DOC-08 | T-06-03 / spend | core demo runs with only `OPENROUTER_API_KEY` | unit + manual | `uv run pytest tests/test_config.py -q`; live check in `/gsd-verify-work` | ✅ code / ⚠️ live pending | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_docs.py` (or extend `tests/test_config.py`) — assert `docs/architecture.md` exists, README contains the canonical eval command, failure-tree/quickstart paths resolve. Covers DOC-01/02/03.
- [ ] *(No framework install needed — pytest is already configured.)*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Core demo with only `OPENROUTER_API_KEY` | DOC-08 | Requires a real OpenRouter key; no network in CI | Launch `uv run python app.py` with only `OPENROUTER_API_KEY` set; confirm app loads and a live run streams. Final confirmation in `/gsd-verify-work`. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
