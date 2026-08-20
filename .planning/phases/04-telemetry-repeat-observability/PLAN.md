# Phase 4 — Telemetry, Repeat, and Observability

## Overview

Goal: Provide honest, normalized telemetry for inference runs, support repeat/cache observations, and optionally integrate Langfuse traces so reviewers can compare recent runs and reproduce behavior.

Scope: Normalize telemetry fields (provider/model, latency, tokens, cost, fallback metadata), implement repeat/cache observation APIs, add Langfuse trace creation when configured, and build UI panels for comparing recent runs.

Out of scope: Scaling to high throughput or long-term storage beyond demo needs.

## Success Criteria

- Every run produces a normalized telemetry record with fields: provider, model, latency_ms, tokens (optional), cost (optional), fallback_attempts, trace_id (optional).
- A 'Repeat' button in the UI can re-run a previous run with the same inputs and provenance metadata and report differences.
- Recent run history supports a comparison view of at least 5 runs with sortable columns.
- Langfuse traces created when configured and disabled explicitly when missing credentials.
- Automated tests that validate telemetry normalization, repeat behavior, and trace creation toggles.

## Tasks

- Telemetry schema: define normalized fields and types. (Owner: @ish)
- Storage: implement short-term in-memory store for recent runs and repeat metadata. (Owner: @ish)
- Repeat API: implement re-run endpoint that accepts a run id and reproduces the original call with preserved provenance. (Owner: @ish)
- UI: add comparison panel and Repeat button in run history rows. (Owner: @ish)
- Langfuse: add optional trace creation and toggles. (Owner: @ish)
- Tests: add pytest coverage for telemetry normalization, repeat, and Langfuse toggle behavior. (Owner: @ish)

## Dependencies

- Phase 2 streaming inference and Phase 3 routing/fallback features (completed)
- Existing telemetry and routing modules

## Risks

- Replaying runs may need deterministic inputs; provider behavior could be non-deterministic.
- Langfuse integration may require careful handling of secrets and rate limits.

## Verification

- Unit tests for normalization and repeat behavior.
- Manual run: create a sequence of runs, replay one, and assert telemetry shows consistent provenance and observed differences.

## Timeline

- Design and schema: 1 day
- Implementation (storage + API): 2 days
- UI + Langfuse optional integration: 2 days
- Tests and polish: 1 day

## Notes

Keep Langfuse optional and focus on clear provenance for replayed runs.
