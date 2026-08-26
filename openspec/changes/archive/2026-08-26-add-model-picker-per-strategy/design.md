## Context

The strategy section of `src/openrouter_demo/ui.py` (around lines 1095–1130) currently renders a single `ui.radio` whose option labels embed both the strategy name and the hardcoded model short name (e.g. `"Cost: deepseek-v4-flash"`). `run_request` (around line 958) reads the model id with `model_id = STRATEGY_MODELS[selected_strategy.name]` — a dict-of-string lookup. `routing.RoutingStrategy.model` is dead at runtime but still exists and is overridden per-call by `_strategy_with_model`. See `proposal.md` for motivation; see `docs/superpowers/plans/2026-08-21-ponytail-cleanup.md` for the prior cleanup that established `STRATEGY_MODELS` as the live source of truth.

## Goals / Non-Goals

**Goals:**
- Expose three models per strategy as a UI choice without changing the inference flow, the telemetry surface, or the routing payload shape.
- Keep the live model source of truth in a single Python literal so the test `test_strategy_models_are_hard_coded_by_strategy` can pin it with one equality assertion.
- Make the picker robust to mid-session strategy switching (selecting Cost after Intelligence must repopulate the picker with Cost's models, not leak Intelligence's selection).

**Non-Goals:**
- Introducing a config layer (env var, .ini, etc.) — every other strategy detail is a literal, and only this one string is being widened, not made dynamic.
- Persisting the chosen model across page reloads (no localStorage, no server-side memory beyond the live NiceGUI session).
- Hiding the model id in the telemetry row — the picker selection must still surface in `InferenceRun.model` exactly as the current single-model case does.
- Touching `routing.py`, `client.py`, `models.py`, or `evals.py`.

## Decisions

- **Data shape: `dict[str, list[str]]`, list is the display order.** Picker shows models in the order listed, so the cost strategy defaults to `deepseek/deepseek-v4-flash-0731` (the model we just landed in the previous change) and the intelligence strategy defaults to `anthropic/claude-opus-5`. Display order = default = "first option in the list". No separate `default` field needed.
  - *Alternative considered:* `dict[str, dict[str, str]]` with `{default, alternatives}` keys. Rejected — adds a structural concept ("is this the default or an alternative?") that doesn't show up in the UI and forces tests to assert two things per strategy. The "first item is default" convention is one line shorter and matches NiceGUI's `ui.select` default behavior.
  - *Alternative considered:* keep `dict[str, str]` for the default and add a separate `STRATEGY_ALTERNATIVES: dict[str, list[str]]`. Rejected — two parallel maps that must stay in sync reintroduces exactly the kind of dual-source-of-truth problem the ponytail cleanup just removed.

- **Model picker placement: directly below the strategy radio on the same card, labelled "Model".** Picks stay visually adjacent to the strategy that owns them. No new section heading, no card split.
  - *Alternative considered:* an inline dropdown inside each radio option. Rejected — NiceGUI radio option labels can't host interactive controls cleanly, and the inline approach would hide the model short name behind a click.

- **Strategy radio labels: just the strategy name (`"Cost"`, `"Intelligence"`).** Model identity lives in the picker, not in the radio label. This removes the duplicated `STRATEGY_MODEL_SHORT_NAMES[STRATEGY_MODELS[s.name]]` lookup from the option expression and keeps each UI element responsible for one thing.
  - *Alternative considered:* keep `"Cost: <default-model>"` and have the picker sit next to the radio. Rejected — the label and the picker would show the same info twice and the label would lie the moment the user picks a non-default model.

- **Picker defaults to the first option in the strategy's list, and resets to first when the user switches strategies.** A `selected_models: dict[str, str]` keyed by strategy name lives on the UI state (the `_UIState` dataclass around line 200, or a new local in `render_home_page`). `update_strategy_display` writes the first option of the new strategy into the picker whenever the strategy radio changes; `run_request` reads the picker's current value.
  - *Alternative considered:* persist the user's per-strategy choice across strategy switches (each strategy remembers the last model the user picked for it). Rejected for v1 — the proposal mentions this as a possible enhancement but it adds a `dict` field on state plus extra reset logic. Demo-friendly enough to defer.
  - *Actual decision (recording for the apply phase):* the picker's value is set fresh from `STRATEGY_MODELS[strategy.name][0]` each time the strategy radio changes. Per-strategy persistence is the documented follow-up if the demo later needs it.

- **`run_request` reads from the picker, with a defensive fallback.** `model_id = model_select.value or STRATEGY_MODELS[selected_strategy.name][0]` — if the picker is somehow empty (test harness, async race during render), fall back to the first option in the strategy list. Avoids a `KeyError` or empty-string model that would silently break the call.
  - *Alternative considered:* raise on empty picker. Rejected — the demo must not crash; falling back to the same default the picker would show is the safest behavior.

- **Short display names follow the existing convention**: drop the provider prefix, drop any `:free`/`paid`/snapshot-date suffix only if it would crowd the Swiss/Grid telemetry row. Concretely: `ling-3.0-flash`, `solar-pro4`, `glm-5.2`, `deepseek-v4-pro`. The two DeepSeek variants disambiguate by `-flash` vs `-pro` in the short name; if both ever land on the same telemetry row, the full id is also rendered.
  - *Alternative considered:* use the full model id in the picker. Rejected — `deepseek/deepseek-v4-flash-0731` is wider than the strategy radio button and breaks the Swiss/Grid rules of the existing telemetry row.

- **No new spec.** This change is a UX expansion + data-shape refactor; the runnable behavior (one inference call per click, same telemetry, same routing payload shape) is unchanged. Per the openspec skill's own guidance — *"Do not invent a requirement just to satisfy validation"* — the change sets `skip_specs: true`.

## Risks / Trade-offs

- [Risk] A user clicks the strategy radio, the picker repopulates, but `run_request` already captured a stale `model_id` from the previous selection. → Mitigation: `run_request` always reads the picker at click time, never captures the model id before the click.
- [Risk] The four new model ids may not be live on OpenRouter for this account right now. → Mitigation: same posture as the previous change — the demo's existing error surface already renders OpenRouter errors next to the response panel. Failure is visible, not silent.
- [Risk] `test_strategy_models_are_hard_coded_by_strategy` becomes a longer literal that drifts from `STRATEGY_MODEL_SHORT_NAMES` if a future model id is added to the list but not the short-name map. → Mitigation: add a sibling assertion in the same test (`assert set(STRATEGY_MODEL_SHORT_NAMES).issuperset({m for ms in STRATEGY_MODELS.values() for m in ms})`) so the test catches any list entry without a short name.
- [Risk] The picker's default (`STRATEGY_MODELS[strategy.name][0]`) may pick a model the interviewer hasn't heard of. → Mitigation: ordering is deliberate — the first option in each list is the most familiar / most defensible (DeepSeek Flash, Claude Opus). Subsequent options are the discovery.
- [Risk] Picker persistence is per-session only; restarting the app resets all selections. → Mitigation: documented non-goal; matches the rest of the demo's "no persistence" stance (see `_UIState` and `SQLiteRunHistory` boundaries).

## Migration Plan

No data migration. Deploy is the commit itself. Rollback is `git revert` of the change (restores `dict[str, str]`, drops the picker, restores the old radio labels).

Verify after deploy:
1. `uv run pytest tests/test_ui.py::test_strategy_models_are_hard_coded_by_strategy` passes.
2. New picker test passes.
3. App starts; Cost strategy defaults the picker to `deepseek-v4-flash`; switching to Intelligence defaults the picker to `claude-opus-5`; running each strategy against any of its three models returns a real response with the chosen model id in the telemetry row.

## Open Questions

None. The one design call that needed user input (persist per-session vs. reset on strategy switch) was resolved in the proposal: reset on strategy switch for v1, per-strategy persistence deferred.
