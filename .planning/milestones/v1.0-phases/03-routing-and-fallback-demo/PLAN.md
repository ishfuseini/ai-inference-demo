# Phase 3 — Routing and Fallback Demo

## Overview

Goal: Show routing strategies and robust fallback behavior in the demo so that production inference can be explained and defended within a five-minute interview.

Scope: Implement strategy selection UI, routing to multiple models/providers, deterministic and probabilistic fallback behaviors, observable telemetry for routing decisions, and an end-to-end demo scenario with sample prompts and expected outputs.

Out of scope: Large-scale load testing, production deploy automation, and non-demo integrations for now.

## Success Criteria

- Interactive UI to select routing strategy (priority, round-robin, latency-based) and configure fallback rules.
- Demonstration scenario that exercises at least two failure/fallback paths and shows telemetry for decisions.
- Automated verification script (pytest) that can simulate primary failure and assert fallback path executed and metrics emitted.
- Documentation: updated demo README and a short (`docs/phase-3.md`) explainer.

## Tasks

- UX: Add strategy selection controls and fallback rule editor in demo UI. (Owner: @ish)
- Backend: Implement routing layer that picks provider/model based on selected strategy and returns routing metadata. (Owner: @ish)
- Telemetry: Emit routing decision events and fallback events to the existing telemetry pipeline. (Owner: @ish)
- Tests: Add pytest-based verification to simulate provider failure and assert fallback behavior. (Owner: @ish)
- Docs: Write docs/phase-3.md and update demo README with instructions. (Owner: @ish)

## Dependencies

- Phase 2: streaming inference console (completed)
- Existing telemetry pipeline (already present)

## Risks

- Complexity in simulating different provider failures in tests.
- Time required to instrument telemetry precisely for clear demo visuals.

## Verification

- Manual run-through checklist in README demonstrating strategy switching and fallback.
- Automated pytest simulating primary provider failure and asserting fallback.

## Timeline

- Draft implementation and UI mock: 2 days
- Backend + telemetry + tests: 3 days
- Docs and polish: 1 day

## Notes

Keep Langfuse optional and surface raw provider responses for inspectability.
