# Milestones

## v1.0 MVP (Shipped: 2026-08-20)

**Closeout type:** verified_closeout
**Known verification overrides:** 0 newly acknowledged, 2 carried forward from a prior close (see STATE.md Deferred Items)
**Git range:** `1f1c504` → `417535b` (104 commits)
**Timeline:** 3 days (2026-08-18 → 2026-08-20)
**LOC:** 2,188 src / 2,664 tests
**Quality gates:** 105 tests pass, ruff clean

**Phases completed:** 6 phases, 15 plans, 28 tasks

**Key accomplishments:**

1. Package legitimacy gate, setup shell, config, and import boundary guards — reviewer can `uv sync && uv run python app.py` with clear missing-key guidance.
2. Streaming UI state seam turns injected OpenRouter stream events into response text, telemetry evidence, and bounded run history records.
3. NiceGUI streaming console submits default-route prompts, shows response/telemetry evidence, and records recent inference runs.
4. Strategy registry, provider-aware payloads, and model types wired into the UI selector end-to-end.
5. Client-side two-attempt fallback orchestration with primary failure evidence preserved in the UI.
6. Normalized telemetry end-to-end: one run records cache/trace/router fields from stream to telemetry panel, with conditional Langfuse tracing that never blocks inference.
7. Repeat/cache scenario: two-run observation reports provider cache metadata only when present, otherwise observed first-vs-second latency and cost, with a Repeat UI action.
8. Persistence round-trip preserves Unavailable sentinels, cache/trace fields, and fallback/repeat evidence; the history UI gains Cache/Trace columns and a comparison view; the dead telemetry schema is removed.
9. Delivered a runnable deterministic eval CLI that executes 5 checked-in cases against two routing strategies and reports pass/fail with a score reason plus honest latency/token/cost/trace telemetry, by composing the existing stream/trace/telemetry path rather than building a new one.
10. Docs slice: rewritten README, promoted architecture guide, relocated failure tree with UI copy pinned to literal `ui.py` constants.
11. Guard-tests slice: DOC-04 UI-framing guard and DOC-05 focused-coverage guard enforced by tests, not just research.
12. Quality-gate confirmation: 105 tests pass, ruff clean, single-credential demo confirmed via live UAT (9/9 passed).

---
