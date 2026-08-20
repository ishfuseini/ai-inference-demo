# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-08-20
**Phases:** 6 | **Plans:** 15 | **Tasks:** 28 | **Timeline:** 3 days

### What Was Built
- Runnable NiceGUI app with streaming OpenRouter inference, routing strategies (default/cost/latency), and client-side two-attempt fallback
- Normalized telemetry with honest Unavailable sentinels, conditional Langfuse tracing, and SQLite persistence with comparison view
- Deterministic eval CLI (5 cases, 2 strategies) with keyword scoring and honest latency/token/cost/trace telemetry
- Rewritten README, architecture guide, failure tree, and UI copy guards pinned to literal source constants
- 105 tests across 11 test modules, ruff clean

### What Worked
- Vertical MVP mode kept every phase demoable — no "big bang" integration risk
- Direct OpenRouter HTTP calls kept all provider routing and metadata inspectable in the UI
- `Unavailable` sentinel pattern enforced metadata honesty from models through persistence to UI
- Conditional Langfuse tracing (`config.langfuse_ready` gate) never blocked inference
- Guard tests (test_docs.py, test_ui.py) caught UI/docs drift before it reached the interviewer
- Seed docs in `docs/` and `data/` grounded every phase — no rework from missing context

### What Was Inefficient
- Phase 4 verification report (04-VERIFICATION.md) was missing entirely — had to reconstruct from SUMMARY.md files at milestone close
- Phase 6 verification report (06-VERIFICATION.md) lacked YAML frontmatter — init.manager couldn't parse it until fixed
- Milestone closeout required manual reconstruction of two verification artifacts that should have been created during phase execution

### Patterns Established
- **Unavailable sentinel over None/zero**: `UNAVAILABLE` constant serializes to `"__unavailable__"` and round-trips through dict/SQLite — distinguishes "not reported" from "zero"
- **Cache honesty**: cache hit/write derived ONLY from `usage.prompt_tokens_details`, never from latency/cost heuristics
- **Guard tests for docs/UI**: tests pin UI copy to literal `ui.py` constants and verify docs match implementation
- **Client-side fallback**: two-attempt orchestration preserves primary failure evidence; server-side `models` array rejected because it hides primary failure
- **Eval composition over construction**: eval CLI reuses existing stream/trace/telemetry path rather than building a parallel one

### Key Lessons
1. Create verification reports (VERIFICATION.md) with proper YAML frontmatter at phase completion — not at milestone close
2. Vertical MVP mode is the right default for interview demos — every phase ships a demoable slice
3. Metadata honesty (Unavailable sentinel) must be a data-layer pattern, not a UI-layer afterthought
4. Guard tests that pin UI copy and docs to source constants catch drift cheaply

### Cost Observations
- Model mix: primarily haiku-class models for demo inference (cost-bounded by design)
- Sessions: 3-day build across 6 phases
- Notable: default prompts and eval cases kept small and bounded per constraint

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 3 days | 6 | Initial MVP build — Vertical MVP mode, guard tests, Unavailable sentinel pattern |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 105 | 11 modules | 0 (all from declared stack) |

### Top Lessons (Verified Across Milestones)

1. Verification artifacts must be created and frontmatter-validated at phase completion, not deferred to milestone close
2. Vertical MVP phases produce interview-demonstrable value at every step — no integration risk
3. Metadata honesty is a data-layer pattern (Unavailable sentinel) that propagates correctly through persistence and UI
