---
status: passed
phase: 01-runnable-skeleton-and-config
threats_open: 0
reviewed_files:
  - .planning/REQUIREMENTS.md
  - .planning/phases/01-runnable-skeleton-and-config/01-01-PLAN.md
  - .planning/phases/01-runnable-skeleton-and-config/01-01-SUMMARY.md
  - .planning/phases/01-runnable-skeleton-and-config/01-02-PLAN.md
  - .planning/phases/01-runnable-skeleton-and-config/01-02-SUMMARY.md
  - .planning/phases/01-runnable-skeleton-and-config/01-03-PLAN.md
  - .planning/phases/01-runnable-skeleton-and-config/01-03-SUMMARY.md
  - .planning/phases/01-runnable-skeleton-and-config/01-VALIDATION.md
  - app.py
  - src/openrouter_demo/__init__.py
  - src/openrouter_demo/client.py
  - src/openrouter_demo/config.py
  - src/openrouter_demo/evals.py
  - src/openrouter_demo/history.py
  - src/openrouter_demo/models.py
  - src/openrouter_demo/routing.py
  - src/openrouter_demo/scenarios.py
  - src/openrouter_demo/telemetry.py
  - src/openrouter_demo/ui.py
  - .env.example
  - pyproject.toml
  - uv.lock
  - README.md
  - tests/test_client.py
  - tests/test_config.py
  - tests/test_imports.py
  - tests/test_phase1_guards.py
generated: 2026-08-19T16:36:51Z
---

# Phase 01 Security Enforcement

## Scope

Phase 01 covers `SETUP-01` through `SETUP-06`: dependency installation, local NiceGUI launch, env-only credential setup, optional Langfuse readiness, missing OpenRouter guidance, and separated package layout. This review checked the Phase 01 plans/summaries, validation strategy, and current repo files touched by the Phase 01 setup/package scaffold.

Later-phase code is now present in the current checkout: `src/openrouter_demo/client.py` contains a live OpenRouter streaming helper (`OPENROUTER_CHAT_COMPLETIONS_URL`, `stream_chat_completion`) and `tests/test_client.py` covers it with `httpx.MockTransport`. For this Phase 01 gate, that later network-capable helper is treated as out of Phase 01 entrypoint scope; the Phase 01 app surface remains non-live because `app.py` only loads config, builds the NiceGUI shell, and runs the UI, while `src/openrouter_demo/ui.py` renders a disabled `Run Inference` button and states that no Phase 1 request is sent.

## Threat Inventory

| Threat | Severity | Files | Status | Evidence |
|---|---:|---|---|---|
| T-01-01-SC: tampered dependency selection before install | high | `01-01-PLAN.md`, `01-01-SUMMARY.md`, `pyproject.toml`, `uv.lock` | closed | Plan required a blocking package legitimacy checkpoint; summary records human approval for `uv`, `nicegui`, `httpx`, `langfuse`, `pytest`, and `ruff`. `pyproject.toml` lists only those runtime/dev dependencies and `uv.lock` records the root package dependencies as `httpx`, `langfuse`, `nicegui`, `pytest`, and `ruff`. |
| T-01-01-01: spoofed PyPI package identity | medium | `01-01-SUMMARY.md` | closed | Summary records registry checks and approval for each planned package before dependency files or installs were created. |
| T-01-01-02: missing approval trail | low | `01-01-SUMMARY.md` | closed | Summary records `Status: Complete`, `Result: approved`, verification commands, and that no dependency files/lockfiles/installs were created before approval. |
| T-01-02-01: committed credential material in examples/docs | high | `.env.example`, `README.md`, `tests/test_config.py` | closed | `.env.example` has only comments plus empty assignments for `OPENROUTER_API_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL`. README setup uses empty `export ...=` examples. `tests/test_config.py` asserts `.env.example` assignments end with `=`. Secret-pattern search found only constant names and test dummy values, not real key material. |
| T-01-02-02: config leaks secret values | medium | `src/openrouter_demo/config.py`, `src/openrouter_demo/ui.py`, `tests/test_config.py` | closed | `AppConfig` contains readiness booleans and missing-name tuples only. `load_config()` returns booleans/missing names from `os.environ` or an injected mapping, not secret values. UI copy explicitly says credential values are not displayed when present. |
| T-01-02-03: missing `OPENROUTER_API_KEY` crashes local startup | medium | `app.py`, `src/openrouter_demo/config.py`, `src/openrouter_demo/ui.py`, `tests/test_config.py` | closed | `load_config({})` models the missing key as `openrouter_ready=False` and `missing_required=(OPENROUTER_API_KEY,)`. `app.py` does not require the key before `ui.run()`. UI renders setup guidance when the key is missing. |
| T-01-02-04: unsafe rendering of setup/prompt text | medium | `src/openrouter_demo/ui.py` | closed | Phase 01 UI uses NiceGUI `ui.label`, `ui.textarea`, `ui.button`, `ui.badge`, and cards; raw HTML/markdown rendering searches returned no matches in app/source/tests/docs. The prompt textarea is present, but the run button is disabled and has no live request path in Phase 01 UI. |
| T-01-02-05 / T-01-02-SC: dependency resolution without the approved package gate | high | `01-01-SUMMARY.md`, `01-02-SUMMARY.md`, `pyproject.toml`, `uv.lock` | closed | Plan 01-02 depended on Plan 01-01 approval. Plan 01-02 summary says `uv.lock` was generated by `uv sync` after adding approved dependency metadata; root lock metadata matches the approved package set. |
| T-01-03-01: Phase 01 import/package scaffold triggers live OpenRouter calls or leaks API key | high | `app.py`, `src/openrouter_demo/client.py`, `src/openrouter_demo/ui.py`, `tests/test_client.py` | closed for Phase 01 entrypoint; superseded by later phase implementation | Current `client.py` does contain a live streaming helper and sends `Authorization: Bearer {api_key}` when explicitly called; that is later-phase network functionality now present in the repo, not invoked by the Phase 01 local shell. `app.py` calls only `load_config()` and `build_app(config)`. `ui.py` disables `Run Inference` and states live inference starts in Phase 2. `tests/test_client.py` uses `httpx.MockTransport`, so its security evidence does not require live network calls. |
| T-01-03-02: Langfuse readiness creates traces or exposes tracing secrets | medium | `src/openrouter_demo/telemetry.py`, `src/openrouter_demo/config.py`, `tests/test_imports.py`, `tests/test_phase1_guards.py` | closed | `trace_readiness_from_config()` returns only `TraceReadiness(enabled, detail)`. No `get_client(`, `.trace(`, `.start_span(`, or `.generation(` calls were found in implementation source. Guard tests assert those APIs are absent. |
| T-01-03-03: scaffold adds FastAPI product layer or database surface | medium | `app.py`, `src/openrouter_demo/**`, `tests/test_phase1_guards.py` | closed | Source search found no `fastapi`, `sqlite3`, `sqlalchemy`, `psycopg`, or `asyncpg` imports in implementation files. Guard tests assert those imports remain absent. |
| T-01-03-04: eval command fabricates scores | low | `src/openrouter_demo/evals.py`, `tests/test_imports.py` | closed | `evals.main()` raises `PhaseNotImplementedError("Deterministic eval execution belongs to Phase 5.")`; tests verify the Phase 5 ownership error and that no `evals/cases.json` exists in Phase 1. |
| T-01-03-SC: new install during import-boundary plan | high | `01-03-SUMMARY.md`, `pyproject.toml`, `uv.lock` | closed | Plan 01-03 summary lists only package boundary modules/tests and says later behavior remains explicit; no new dependency files were introduced by that plan. Dependency surface remains the approved `pyproject.toml`/`uv.lock` package set. |

## Mitigations Verified

- **Secret handling:** `.env.example` and README provide variable names with empty assignments only; no real OpenRouter or Langfuse credentials were found in reviewed setup/source/test files. Config state never stores or returns secret values.
- **Optional credentials:** Langfuse variables are optional. `load_config()` reports incomplete Langfuse env as `langfuse_ready=False`, and telemetry readiness returns a disabled detail without creating a trace.
- **Network call absence/presence:** Phase 01 app/UI do not invoke a live request. Current source does contain later-phase OpenRouter streaming code in `client.py`; that presence is documented here and should be covered by Phase 02 security/verification, not hidden as a Phase 01 stub.
- **Config validation honesty:** Missing required OpenRouter credential is a setup state, not a startup exception. Unavailable metadata uses `UNAVAILABLE`, not numeric zero.
- **Dependency/package surface:** Runtime dependency declarations are limited to `nicegui`, `httpx`, and `langfuse`; dev dependencies are `pytest` and `ruff`; `uv.lock` records exact resolved packages from the approved root set.
- **Docs and setup copy:** README and `.env.example` do not ask reviewers to paste key material into committed files. README instructs exported environment variables and notes `.env` parsing is not used in Phase 1.

## Open Threats

No unresolved high or medium Phase 01 threats remain.

## Low / Informational Observations

- The current checkout has moved beyond the original Phase 01 non-live client stub: `client.py` now contains live OpenRouter request construction. This is not an open Phase 01 setup-shell threat because the Phase 01 entrypoint/UI do not call it, but Phase 02 security review should assess request construction, auth header handling, timeout behavior, and prompt/response display.
- The existing `tests/test_phase1_guards.py` no longer contains the original no-OpenRouter-endpoint assertion described in Plan 01-03; it still guards against FastAPI, database imports, and Langfuse trace creation. This is acceptable for the current multi-phase repo only if later-phase network behavior is verified in its own phase gate.

## Conclusion

Phase 01 security status is `passed`: the local runnable skeleton handles credentials as env-only readiness state, keeps examples free of committed key material, does not require optional Langfuse credentials, keeps startup non-blocking when OpenRouter is missing, avoids extra product surfaces such as FastAPI/database layers, and preserves an approved dependency surface. `threats_open` is `0` for Phase 01 high/medium threats.