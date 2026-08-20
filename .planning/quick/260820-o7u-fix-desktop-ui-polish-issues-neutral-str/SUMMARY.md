---
status: complete
completed: 2026-08-20
---

# Summary

Completed desktop evidence-table polish.

Changes:

- Strategy select now uses a neutral black focus underline and paper-colored dropdown highlight instead of violet.
- Comparison now renders in its own tab beside Telemetry and Run History.
- Run History no longer contains an embedded Comparison section.
- Table scrollers are thin and scoped to `.demo-grid-scroll`.
- Trace columns were removed from Run History and Comparison.
- Trace URLs now live on the run-number link when a run has a Langfuse trace URL.

Verification:

- `node .agents/skills/impeccable/scripts/detect.mjs --target src/openrouter_demo/ui.py`
- `uv run ruff check .`
- `uv run pytest`
- Desktop render inspection confirmed:
  - Strategy selected row highlight is neutral paper/black.
  - Tabs include Telemetry, Run History, and Comparison.
  - Run History headers exclude Trace.
  - Comparison headers exclude Trace and include Run.
  - Run number links open trace URLs in a new tab.
  - Table scrollbars are `thin` / `4px`.
