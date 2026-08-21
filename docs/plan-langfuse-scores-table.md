# Plan: Langfuse Eval Scores Table in UI

> **Status:** Approved — ready for implementation
> **Created:** Previous session (context summary)
> **Purpose:** Add a full-width "Evaluation Scores" card to the NiceGUI UI that fetches and displays individual Langfuse eval scores in a table.

## TL;DR

Add a full-width "Evaluation Scores" card below the existing prompt/response two-column row in the NiceGUI UI. The card fetches individual Langfuse scores via the **v3 Scores API** (`GET /api/public/v3/scores`) using Basic Auth with the existing Langfuse env vars. Scores render in a table with columns: Name, Type, Value, Trace, Timestamp. Long evaluator comments are truncated with tooltip. When Langfuse is disabled (no credentials), the card shows a visible "tracing disabled" message — never blocks inference.

---

## Architecture Decision: v3 Scores API vs Metrics API

The user selected "Live Metrics API" as the data source. However, the Langfuse **Metrics API** (`GET /api/public/v2/metrics`) returns **aggregations** (sum, avg) grouped by dimensions — it cannot list individual score objects with name/value/comment/traceId per row. The correct endpoint for listing individual scores is the **v3 Scores API** (`GET /api/public/v3/scores`), which returns a paginated list of individual score objects with all fields: `id`, `traceId`, `name`, `value`, `dataType`, `comment`, `source`, `timestamp`, `observationId`, `traceName`, etc. The checked-in export JSON files in `evals/` confirm this field structure exactly.

The plan therefore uses `GET /api/public/v3/scores` to fetch individual scores, which is what the table needs.

---

## Current Codebase Context (confirmed)

### File line numbers (verified at plan-writing time)

| File | Key locations |
|------|---------------|
| `src/openrouter_demo/models.py` | `Unavailable` sentinel class + `UNAVAILABLE` constant + `_UNAVAILABLE_SENTINEL = "__unavailable__"`, `serialize_value()`/`deserialize_value()` functions, `TelemetryEvidence(frozen=True)` with `to_dict()`/`from_dict()` classmethod (~line 105), `AttemptRecord` after `TelemetryEvidence` |
| `src/openrouter_demo/telemetry.py` | `TraceOutcome(frozen=True)` dataclass with `status`/`trace_id`/`trace_url` (~line 12), `record_trace()` async function (~line 47, returns disabled if not `config.langfuse_ready`, enabled via SDK, failed via broad `except` with `# noqa: BLE001` comment) |
| `src/openrouter_demo/ui.py` | `_DESIGN_CSS` (43–516), `_format_metadata()` at 524, `_format_cost()` at 528, `_strategy_with_model()` at 532, `_heading(text, *, level, classes)` at 536, `SamplePrompt` dataclass at 541, `EVAL_DESCRIPTION` at 562, `_UIState` dataclass at 583 (fields: `is_running`/`last_run`/`response`/`response_status`), `build_app()` at 696, `response_panel()` @ui.refreshable at 725, `refresh(panel)` helper at 739, `run_request()` async handler at 758+, eval description `ui.html(EVAL_DESCRIPTION)` at 823, two-column row with prompt card + response card at 847–915, **file ends at line 916** (`response_panel()` is the last line) |
| `src/openrouter_demo/config.py` | `AppConfig(openrouter_ready, langfuse_ready)`, env var constants `OPENROUTER_API_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`, `load_config()` with dotenv. No changes needed. |
| `src/openrouter_demo/formatting.py` | `is_unavailable()`, `format_cost/number/latency/trace` with `*, unavailable: str` pattern |
| `evals/*.json` | Score JSON structure: `id`, `traceId`, `timestamp`, `name`, `dataType`, `value`, `stringValue`, `comment`, `observationId`, `traceName`, `source`, `metadata` |

### Patterns to reuse

- `TraceOutcome` dataclass + `record_trace()` three-state pattern in `telemetry.py` — direct template for `FetchOutcome` + `fetch_langfuse_scores()`
- `@ui.refreshable def response_panel()` in `ui.py:725` — direct template for `eval_scores_panel()`
- `_UIState` dataclass in `ui.py:583` — extend with scores state fields
- `_heading()` helper in `ui.py:536` — for section headings
- `ui.card().classes("... demo-card")` pattern in `ui.py:851` — for the scores card container
- `refresh(panel)` helper in `ui.py:739` — for refreshing the panel after fetch
- `_DESIGN_CSS` table styles in `ui.py:43–516` — reuse `.demo-table` classes
- `format_trace()` in `formatting.py` — for formatting trace ID display

### NiceGUI + Quasar CSS notes (from project memory)

NiceGUI 3.16+ uses Quasar which injects brand colors as **inline styles on `<body>`**. Override Quasar brand variables at the `body` level with `!important`:
```css
body {
  --q-primary: #7B23D4 !important;
  --q-positive: #15803D !important;
  --q-negative: #B91C1C !important;
  --q-warning: #B45309 !important;
}
```
CSS layer order: `@layer theme, base, quasar, nicegui, components, utilities, overrides, quasar_importants;` — `quasar_importants` uses `!important`, so unlayered `!important` (via `ui.add_head_html`) is needed to win.

---

## Steps

### Phase 1: Data Layer — Langfuse Score Fetching

**1.1** Add `LangfuseScore` frozen dataclass to `src/openrouter_demo/models.py`
- Insert: after `TelemetryEvidence` (~line 105), before `AttemptRecord`
- Fields matching the v3 API/export JSON: `id: str`, `trace_id: str`, `timestamp: str`, `name: str`, `data_type: str` (BOOLEAN/NUMERIC/CATEGORICAL/TEXT), `value: float | str | bool`, `string_value: str | None`, `comment: str`, `observation_id: str | None`, `trace_name: str | None`, `source: str`
- Include a `display_value` property that returns the human-readable value: for BOOLEAN → "True"/"False", for NUMERIC → the number, for CATEGORICAL/TEXT → `string_value`
- Include `to_dict()` / `from_dict()` round-trip methods following the `TelemetryEvidence` pattern (with `serialize_value`/`deserialize_value` for any Unavailable fields)

**1.2** Add `fetch_langfuse_scores()` async function to `src/openrouter_demo/telemetry.py`
- Signature: `async def fetch_langfuse_scores(config: AppConfig, *, limit: int = 50) -> FetchOutcome`
- Returns `FetchOutcome(status="disabled", scores=None)` when `config.langfuse_ready` is False
- Reads `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` from `os.environ` directly
- Constructs Basic Auth header: `base64(public_key:secret_key)`
- Uses `httpx.AsyncClient` (already a dependency) with timeout=30s
- GET request to `{base_url}/api/public/v3/scores?limit={limit}&orderBy=timestamp&order=desc`
- Parses JSON response: extract `data` array, map each item to `LangfuseScore`
- Catches all exceptions broadly (`except Exception`) returning `FetchOutcome(status="failed", scores=())` — never blocks the UI, consistent with `record_trace`'s error philosophy
- Add `# noqa: BLE001` comment on the broad except (same as `record_trace`)

**1.3** Add a `FetchOutcome` dataclass to `telemetry.py` (alongside `TraceOutcome`)
- Insert: after `TraceOutcome` (~line 12), before `record_trace`
- Fields: `status: str` ("enabled" | "disabled" | "failed"), `scores: tuple[LangfuseScore, ...] | None`
- This follows the three-state pattern of `record_trace` / `TraceOutcome` and the project's "metadata honesty" constraint — disabled must be distinguishable from empty/failed

*Phase 1 depends on nothing — can start immediately.*

### Phase 2: UI Table Rendering

**2.1** Add CSS styles for the eval scores table to `_DESIGN_CSS` in `src/openrouter_demo/ui.py`
- The existing `_DESIGN_CSS` already contains table styles (`.demo-table`, etc.). Reuse/extend those.
- Add styles for: truncated comment cell (`.demo-score-comment` with `text-overflow: ellipsis`, `max-width`, `white-space: nowrap`, `overflow: hidden`), tooltip via `title` attribute, and a `.demo-score-value--pass`/`--fail` modifier for boolean pass/fail coloring

**2.2** Add state fields to `_UIState` dataclass in `ui.py` (~line 583)
- `is_fetching_scores: bool = False`
- `scores: tuple[LangfuseScore, ...] | None = None` (None = not fetched yet, () = fetched but empty)
- `scores_fetch_status: str = ""` ("" | "disabled" | "failed" | "fetched")

**2.3** Create `@ui.refreshable def eval_scores_panel()` in `build_app()` — modeled directly on `response_panel()` (ui.py:725)
- Heading: "Evaluation Scores" via `_heading(..., level=2, classes="demo-section-heading")`
- Three render states:
  - **Not fetched / disabled**: Show a `ui.label` with "Langfuse tracing is not configured. Set LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and LANGFUSE_BASE_URL to fetch evaluation scores." (mirrors the status-bar readiness pattern)
  - **Fetching**: Show "Loading scores…" label
  - **Fetched**: Render `ui.table(columns=..., rows=...)` with the core columns
- If fetched but zero scores: show "No evaluation scores found yet. Run inference to generate traces, then wait for Langfuse evaluator jobs to score them."

**2.4** Build table columns and rows inside `eval_scores_panel()`
- Columns (5 core): `Name`, `Type`, `Value`, `Trace`, `Timestamp`
- Rows: one row per `LangfuseScore` in `state.scores`, ordered by timestamp desc (API returns them sorted)
- `Name`: `score.name` — truncated comment in `title` attribute
- `Type`: `score.data_type` (BOOLEAN/NUMERIC/CATEGORICAL/TEXT)
- `Value`: `score.display_value` (the human-readable value property)
- `Trace`: truncated `score.trace_id` (first 8 chars + "…") with full ID in `title` attribute; if `trace_name` available, show it as a secondary label
- `Timestamp`: formatted ISO string (could use `datetime.fromisoformat` for local formatting)
- Comment: **not shown as a column** — shown as tooltip on the Name/Value cell

**2.5** Add "Refresh Scores" button in the eval scores card
- `ui.button("Refresh Scores", on_click=fetch_scores_handler).classes("demo-btn-secondary").props("unelevated")`
- Disabled when `state.is_fetching_scores` or when `config.langfuse_ready` is False
- Button placed at top-right of the card header, inline with the heading

**2.6** Implement `async def fetch_scores_handler()` — async on_click handler
- Guards: return early if `config.langfuse_ready` is False or `state.is_fetching_scores`
- Sets `state.is_fetching_scores = True`, refreshes `eval_scores_panel`
- Calls `await fetch_langfuse_scores(config, limit=50)`
- Updates `state.scores` and `state.scores_fetch_status`
- Sets `state.is_fetching_scores = False`
- Calls `refresh(eval_scores_panel)`

**2.7** Place the eval scores card in `build_app()` page layout
- After the two-column `ui.row` (prompt card + response card) ending at ui.py:915, add a new full-width `ui.card().classes("w-full demo-card demo-scores-card")`
- Inside: heading + refresh button (inline row), then `eval_scores_panel()`
- This keeps existing layout intact and gives the table full width

*Phase 2 depends on Phase 1 (needs `LangfuseScore` and `fetch_langfuse_scores`).*

### Phase 3: Testing & Validation

**3.1** Add tests to `tests/test_telemetry.py` for `fetch_langfuse_scores` / `FetchOutcome`
- Test: returns `FetchOutcome(status="disabled", scores=None)` when `langfuse_ready=False`
- Test: returns `FetchOutcome(status="enabled", scores=(...))` with mocked httpx response (use a mock that returns the export JSON structure)
- Test: returns `FetchOutcome(status="failed", scores=())` when httpx raises (mock to raise `httpx.ConnectError`)
- Test: `LangfuseScore.display_value` returns correct string for BOOLEAN (0 → "False"), NUMERIC (5 → "5"), CATEGORICAL ("tone")

**3.2** Add tests to `tests/test_ui.py` for the eval scores panel
- Test: `eval_scores_panel` renders disabled message when `langfuse_ready=False`
- Test: `eval_scores_panel` renders table rows when `state.scores` is populated
- Test: `fetch_scores_handler` updates state and refreshes panel (use fake fetch function)

**3.3** Add `LangfuseScore` model tests to `tests/test_imports.py` or a new `tests/test_models.py`
- Test `to_dict()` / `from_dict()` round-trip preserves all fields

**3.4** Run `ruff check .` and `ruff format .` — ensure no lint errors
**3.5** Run `pytest` — all tests pass
**3.6** Manual verification: start the app with Langfuse credentials, run inference, click "Refresh Scores", verify table populates with real scores

*Phase 3 depends on Phases 1 and 2.*

---

## Relevant Files

| File | Action | Insertion point |
|------|--------|-----------------|
| `src/openrouter_demo/models.py` | Add `LangfuseScore` dataclass | After `TelemetryEvidence` (~line 105), before `AttemptRecord`. Reuse `serialize_value`/`deserialize_value`. |
| `src/openrouter_demo/telemetry.py` | Add `FetchOutcome` dataclass + `fetch_langfuse_scores()` async fn | `FetchOutcome` after `TraceOutcome` (~line 12); function after `record_trace` (~line 47). Import `httpx`, `base64`, `json`, `os`. |
| `src/openrouter_demo/ui.py` | Add CSS, state fields, panel, handler, card | CSS in `_DESIGN_CSS` (43–516); state fields in `_UIState` (583); `eval_scores_panel()` + `fetch_scores_handler()` inside `build_app()` (696+); scores card after two-column row (~915). |
| `src/openrouter_demo/config.py` | No changes | Reference for env var names and `AppConfig.langfuse_ready`. |
| `src/openrouter_demo/formatting.py` | No changes | Reference for `is_unavailable()` pattern. May reuse for formatting score values. |
| `tests/test_telemetry.py` | Add fetch/score tests | |
| `tests/test_ui.py` | Add panel tests | |
| `evals/1787316775021-lf-scores-export-*.json` | Reference | Score JSON structure (fields: id, traceId, timestamp, name, dataType, value, stringValue, comment, observationId, traceName, source) |
| `evals/1787317143236-lf-scores-export-*.json` | Reference | Second reference for CATEGORICAL scores |

---

## Verification

1. `ruff check . && ruff format .` — no lint/format errors
2. `pytest tests/test_telemetry.py -v` — new fetch/score tests pass
3. `pytest tests/test_ui.py -v` — new panel tests pass
4. `pytest` — full suite passes (no regressions)
5. Manual: start app with `uv run python app.py`, confirm "Evaluation Scores" card appears below the two-column row
6. Manual: with Langfuse credentials set, click "Refresh Scores" — table populates with real scores showing Name, Type, Value, Trace, Timestamp columns
7. Manual: without Langfuse credentials — card shows "Langfuse tracing is not configured" message, inference still works
8. Manual: hover over a truncated trace ID or name — tooltip shows full value
9. Manual: verify boolean scores show "True"/"False", numeric show the number, categorical show the string value

---

## Decisions

- **Data source**: Live v3 Scores API (`GET /api/public/v3/scores`), not the Metrics API (which returns aggregations, not individual scores). The export JSON files confirm the field structure the API returns.
- **Endpoint**: `GET /api/public/v3/scores` with Basic Auth, `limit` query param, `orderBy=timestamp&order=desc`. Verified from Langfuse docs referencing this endpoint for reading individual scores.
- **Table placement**: New full-width card below the two-column row. Keeps existing layout intact.
- **Columns**: Core 5 — Name, Type, Value, Trace, Timestamp. Comment not a column; shown as tooltip on the Name/Value cell.
- **Comment display**: Truncated in `title` attribute (native browser tooltip). No expand/modal in v1 — keep it simple.
- **Three-state pattern**: Disabled (no creds) → message; Enabled + fetched → table; Failed (API error) → "Failed to fetch scores" message. Mirrors `record_trace`/`TraceOutcome`.
- **Metadata honesty**: `state.scores = None` means "not fetched yet" (distinguishable from `()` meaning "fetched, zero scores"). `FetchOutcome.status` distinguishes disabled from failed.
- **Scope excluded**: No local persistence of scores (no SQLite table). No live auto-refresh polling. No trace-to-run linking in v1. No comment modal/expand UI.

---

## Further Considerations

1. **Score-to-run linking**: The `trace_id` in Langfuse scores matches `trace_id` in `TelemetryEvidence` stored in SQLite. A future enhancement could cross-reference scores to local runs. Defer to v2.
2. **Auto-refresh**: Currently manual "Refresh Scores" button. Could auto-fetch after each inference run completes (with a small delay for evaluator jobs to finish). Defer to v2.
3. **NiceGUI `ui.table` vs custom HTML**: `ui.table` is the simplest path. If the design system's table styles need more control than `ui.table` allows, fall back to `ui.html()` with a custom `<table>` built from the score data. The existing `.demo-table` CSS classes suggest the design system anticipated tables.
