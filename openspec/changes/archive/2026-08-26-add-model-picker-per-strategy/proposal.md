## Why

Each routing strategy in the demo currently exposes exactly one model (e.g. "Cost → `deepseek/deepseek-v4-flash-0731`"), with no way to swap to an alternative without editing source. We want to give the interviewer a small, in-UI choice of three models per strategy so the demo can show side-by-side routing/metadata differences across comparable models without anyone re-running `sed` on `ui.py`. The options are:

- **Cost** (in display order): `deepseek/deepseek-v4-flash-0731`, `inclusionai/ling-3.0-flash`, `upstage/solar-pro4`
- **Intelligence** (in display order): `anthropic/claude-opus-5`, `z-ai/glm-5.2`, `deepseek/deepseek-v4-pro`

## What Changes

- Reshape `STRATEGY_MODELS` in `src/openrouter_demo/ui.py` from `dict[str, str]` to `dict[str, list[str]]`, with the three models per strategy listed above.
- Extend `STRATEGY_MODEL_SHORT_NAMES` to cover all six model ids (adding `ling-3.0-flash`, `solar-pro4`, `glm-5.2`, `deepseek-v4-pro`).
- Simplify the strategy radio option labels to just the strategy name (e.g. `"Cost"`) — model selection moves to a dedicated picker.
- Add a `ui.select` model picker on the strategy card, populated from the currently selected strategy's list. The picker's value persists across runs within a session and resets to the first model when the user switches to a different strategy.
- Update `run_request` to read the selected model id from the picker (falling back to the first model in the strategy's list if the picker is empty or stale) instead of `STRATEGY_MODELS[strategy.name]` directly.
- Update `tests/test_ui.py::test_strategy_models_are_hard_coded_by_strategy` to assert the new list shape, and add a test that the model picker exists and defaults to the first option per strategy.
- Leave `routing.COST_STRATEGY.model`, `INTELLIGENCE_STRATEGY.model`, and the existing `_strategy_with_model` helper untouched — they already accept an arbitrary model override at the call site.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The set of strategies, the routing payload shape, the streaming flow, telemetry handling, and the request URL all stay the same. The change is a UX/options expansion plus a small data-shape refactor. No spec-level requirement changes — this change opts out of specs (`.openspec.yaml` sets `skip_specs: true`).

## Impact

- `src/openrouter_demo/ui.py` — 3 edits: `STRATEGY_MODELS` (dict shape + entries), `STRATEGY_MODEL_SHORT_NAMES` (4 new entries), the strategy radio label expression, the new model `ui.select` element + handler, and the `model_id = …` line in `run_request`. Estimated ~30–50 lines of new/edited code.
- `tests/test_ui.py` — update one assertion (`test_strategy_models_are_hard_coded_by_strategy`); add one new test for picker presence/default. Possibly one new helper if picker assertion needs to drive the strategy select.
- No API surface change, no client.py change, no new dependencies, no env vars.
- Live runs: each strategy now exposes three pickable models; the inference call, telemetry, and Langfuse trace behave exactly as before, just keyed to whichever model the picker holds at the moment of click.
