# Quick Summary: Evidence Table Polish

## Changes

- Added bottom padding inside the shared evidence table scroll wrapper so the table content has breathing room before the horizontal scrollbar.
- Updated Run History and Comparison grids to use content-sized columns instead of equal-width columns.
- Removed the fixed max width from evidence table cells so desktop columns can adapt to their displayed values.

## Verification

- `uv run ruff check .`
- `uv run pytest tests/test_ui.py`
- `node .agents/skills/impeccable/scripts/detect.mjs --target src/openrouter_demo/ui.py`
