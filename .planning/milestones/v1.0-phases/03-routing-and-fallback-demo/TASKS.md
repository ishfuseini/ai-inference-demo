# Phase 3 Tasks — Routing and Fallback Demo

This file lists the actionable tasks for Phase 3 and links to implementation stubs.

- UX: Add strategy selection controls and fallback rule editor in demo UI. (Owner: @ish)
  - File: src/ui/routing_controls.py (stub)
- Backend: Implement routing layer that picks provider/model based on selected strategy and returns routing metadata. (Owner: @ish)
  - File: src/routing/router.py (stub)
- Telemetry: Emit routing decision events and fallback events to the existing telemetry pipeline. (Owner: @ish)
  - File: src/routing/telemetry.py (stub)
- Tests: Add pytest-based verification to simulate provider failure and assert fallback behavior. (Owner: @ish)
  - File: tests/test_routing_fallback.py (stub)
- Docs: Write docs/phase-3.md and update demo README with instructions. (Owner: @ish)
