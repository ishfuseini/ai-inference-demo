---
status: passed
phase: 02-streaming-inference-evidence
threats_open: 0
reviewed_files:
  - .planning/REQUIREMENTS.md
  - .planning/phases/02-streaming-inference-evidence/02-01-PLAN.md
  - .planning/phases/02-streaming-inference-evidence/02-01-SUMMARY.md
  - .planning/phases/02-streaming-inference-evidence/02-02-PLAN.md
  - .planning/phases/02-streaming-inference-evidence/02-02-SUMMARY.md
  - .planning/phases/02-streaming-inference-evidence/02-VALIDATION.md
  - app.py
  - src/openrouter_demo/client.py
  - src/openrouter_demo/config.py
  - src/openrouter_demo/history.py
  - src/openrouter_demo/models.py
  - src/openrouter_demo/routing.py
  - src/openrouter_demo/ui.py
  - tests/test_client.py
  - tests/test_config.py
  - tests/test_ui.py
generated: 2026-08-19T17:04:01Z
---

# Phase 02 Security Enforcement

## Scope

Phase 02 covers live default-route OpenRouter streaming evidence from a local NiceGUI UI: prompt submission, progressive response display, request metadata, unavailable metadata handling, success/failure state, and run history. Langfuse trace creation, fallback, cache/repeat claims, eval execution, and non-default routing controls remain out of scope.

## Threat Inventory

| Threat | Severity | Files | Status | Evidence |
|---|---:|---|---|---|
| T-02-01: tests or UI accidentally call live OpenRouter without credentials or spend money during automated checks | high | `tests/test_client.py`, `tests/test_ui.py`, `src/openrouter_demo/ui.py` | closed | Client tests inject `httpx.MockTransport`; UI seam tests inject fake async streams. `build_app` leaves `Run Inference` disabled when `config.openrouter_ready` is false, and browser smoke confirmed disabled state with the key unset. |
| T-02-02: OpenRouter API key leaks into UI, config state, logs, or committed files | high | `src/openrouter_demo/config.py`, `src/openrouter_demo/ui.py`, `.env.example`, `README.md` | closed | `AppConfig` stores only readiness booleans and missing variable names. UI copy says credential value is not displayed. Secret-pattern search found variable names and dummy test values only, not committed key material. |
| T-02-03: missing model/provider/token/cost metadata is fabricated as zero-like evidence | high | `src/openrouter_demo/models.py`, `src/openrouter_demo/client.py`, `src/openrouter_demo/ui.py`, `tests/test_client.py`, `tests/test_ui.py` | closed | `UNAVAILABLE` sentinel is preserved by client extraction and `_run_inference`; UI formatters render explicit unavailable copy. Tests assert missing usage stays `UNAVAILABLE` and UI rows show unavailable copy. |
| T-02-04: user prompt or model output is rendered as raw HTML/Markdown and creates injection risk | medium | `src/openrouter_demo/ui.py` | closed | UI uses `ui.label`, `ui.textarea`, buttons, cards, rows, and grid. Search found no `ui.html`, `ui.markdown`, `run_javascript`, or `eval(` in the Phase 02 UI path. |
| T-02-05: mid-stream errors hide partial output or make failure evidence unavailable | medium | `src/openrouter_demo/client.py`, `src/openrouter_demo/ui.py`, `tests/test_client.py`, `tests/test_ui.py` | closed | Client errors carry `partial_text`; `_run_inference` records failed `InferenceRun` with partial text and `Status.FAILED`. Tests cover OpenRouter error payload partial text and UI handler failure partial text. |
| T-02-06: Phase 02 scope creep adds fallback/cache/trace/eval behavior before security gates exist | medium | `src/openrouter_demo/ui.py`, `tests/test_ui.py` | closed | UI exposes default strategy only and states fallback, cache, trace links, and eval execution are reserved for later phases. Search found no implemented cost/latency/custom route controls, fallback simulation, cache-hit claims, trace-link creation, or eval execution controls. |

## Mitigations Verified

- **Credential handling:** API key is read from `os.environ` only inside the guarded click handler and passed to the OpenRouter client; it is not stored in `AppConfig` or rendered.
- **Request construction:** `stream_chat_completion` sends `Authorization: Bearer {api_key}` and `stream: true`; tests assert the header and payload against a mock transport.
- **No live test spend:** Project tests do not require or call live OpenRouter. The browser smoke intentionally unset `OPENROUTER_API_KEY` and confirmed disabled request controls.
- **Output rendering:** NiceGUI text components render prompt/output/metadata text; no raw HTML/Markdown rendering is used.
- **Metadata honesty:** Unavailable metadata stays sentinel-backed through client, handler, telemetry, and render rows.

## Open Threats

No unresolved high or medium Phase 02 threats remain. Live OpenRouter behavior still requires a real `OPENROUTER_API_KEY` for manual demo execution, but the missing-key path is guarded and tested.

## Conclusion

Phase 02 security status is `passed`: credentials remain env-only, automated tests avoid live spend, user/model text is not raw-rendered, unavailable metadata is not fabricated, partial failure evidence is preserved, and later-phase controls are not prematurely implemented. `threats_open` is `0`.
