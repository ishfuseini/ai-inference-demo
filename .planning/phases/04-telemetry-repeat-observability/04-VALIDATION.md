---
phase: 4
slug: telemetry-repeat-observability
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-19
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ≥9.1.1 (via `uv run pytest`) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` — `testpaths = ["tests"]`, `pythonpath = ["src"]` |
| **Quick run command** | `uv run pytest tests/test_telemetry.py tests/test_client.py -q` |
| **Full suite command** | `uv run pytest && uv run ruff check .` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/<touched-file> -q`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | OBS-01/OBS-02 | T-04-01 / — | `TelemetryEvidence` extension is non-breaking; `Unavailable` sentinels never coerce to zero; `X-OpenRouter-Metadata: enabled` header sent; absent metadata → `UNAVAILABLE` (never fabricated) | unit | `uv run pytest tests/test_telemetry.py tests/test_client.py -q` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | OBS-05/OBS-06 | T-04-02 / — | `langfuse_ready=False` → `trace_status="disabled"`, no `get_client()`; trace failure never changes run status; Phase-1 guard updated to allow conditional tracing | unit | `uv run pytest tests/test_telemetry.py tests/test_phase1_guards.py tests/test_imports.py -q` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | OBS-03/OBS-04 | T-04-03 / — | Cache row only when `cached_tokens>0`/`cache_write_tokens>0`; else observed repeat latency/cost delta | unit | `uv run pytest tests/test_repeat.py tests/test_scenarios.py -q` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 2 | OBS-04 | T-04-04 / — | Repeat UI action renders cache metadata only when provider reported it; otherwise latency/cost delta | smoke | `uv run pytest tests/test_ui.py -q` | ✅ | ⬜ pending |
| 04-03-01 | 03 | 3 | OBS-07 | T-04-05 / — | Persistence round-trips sentinels + cache/trace fields + fallback/repeat evidence; no `{"label": "unavailable"}` leak | unit | `uv run pytest tests/test_sqlite_store.py -q` | ❌ W0 | ⬜ pending |
| 04-03-02 | 03 | 3 | OBS-07 | T-04-06 / — | History rows show Cache + Trace columns; comparison grid renders ≥N runs | smoke | `uv run pytest tests/test_ui.py -q` | ✅ | ⬜ pending |
| 04-03-03 | 03 | 3 | — (hygiene) | T-04-07 / — | Remove dead `telemetry_schema.py`; no remaining import of `telemetry_schema`/`RunRecord`/`FallbackAttempt` | unit | `uv run pytest -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_telemetry.py` — normalization + Langfuse toggle behavior (OBS-01, OBS-05/OBS-06)
- [ ] `tests/test_repeat.py` — cache-honesty assertions: cache present vs absent (OBS-03/OBS-04)
- [ ] `tests/test_sqlite_store.py` — round-trip preserves sentinels + new fields (OBS-07)
- [ ] `tests/test_client.py` — extend: metadata header + cache/absence extraction (OBS-02)
- [ ] `tests/test_phase1_guards.py` — update Langfuse guard (currently forbids `get_client(`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live repeat/cache scenario against a real provider | OBS-03/OBS-04 | Cache behavior depends on provider/route metadata; cannot be asserted against a mock | Run the repeat scenario with `OPENROUTER_API_KEY`; confirm cache row appears only when the provider reports `prompt_tokens_details`; otherwise observe latency/cost delta shown |
| Langfuse trace visible in Langfuse UI | OBS-05 | Requires live `LANGFUSE_*` credentials and a real trace round-trip | Run a demo call with Langfuse configured; confirm trace id + link render, then unset credentials and confirm "tracing disabled" |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
