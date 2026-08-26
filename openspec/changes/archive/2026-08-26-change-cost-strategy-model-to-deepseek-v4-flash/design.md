## Context

The cost routing strategy's runtime model is the string value in `STRATEGY_MODELS["cost"]` in `src/openrouter_demo/ui.py`. `routing.COST_STRATEGY.model` (`openai/gpt-4o-mini`) is intentionally not the live value: the previous ponytail-cleanup review confirmed that `STRATEGY_MODELS` is what the UI actually passes to `stream_chat_completion` for the cost strategy, so it is the single source of truth to edit. `STRATEGY_MODEL_SHORT_NAMES` is a parallel map used only for the Swiss/Grid telemetry label; it must stay in lockstep with the long model id. The same hardcoded pair is mirrored by a single equality assertion in `tests/test_ui.py::test_strategy_models_are_hard_coded_by_strategy`, which guards against accidental drift between the two maps and the test fixture. See `proposal.md` for the motivation.

## Goals / Non-Goals

**Goals:**
- Make the cost strategy invoke `deepseek/deepseek-v4-flash-0731` on OpenRouter instead of `openai/gpt-oss-20b:free` with no other behavioral change.
- Keep the cost/intelligence strategy pair, the routing payload shape, telemetry handling, and the UI surface identical.
- Keep the existing hardcoded-model convention (no new env var, no new config knob).

**Non-Goals:**
- Touching `routing.COST_STRATEGY.model`, the `intelligence` strategy, the `default` strategy, or any provider preferences.
- Adding a new capability, a new spec, or any new code path.
- Validating that DeepSeek actually exposes `deepseek-v4-flash-0731` on OpenRouter at runtime — that is an operational concern, not a code concern; a wrong id will surface as an OpenRouter error in the demo and the existing error surface already renders it.

## Decisions

- **Edit `STRATEGY_MODELS["cost"]` in place, do not introduce a config layer.** Every other entry in the map is a literal string; promoting just this one to env/config would create a special-case indirection that costs more clarity than it saves. Adding an env var also makes the demo's `.env.example` start pretending to be configurable when the rest of the file isn't.
- **Mirror the change in `STRATEGY_MODEL_SHORT_NAMES` with the short label `deepseek-v4-flash`.** This matches the existing convention (`openai/gpt-oss-20b:free` → `gpt-oss-20b`): drop the `:free`/`paid` suffix, drop the `provider/` prefix, drop the date suffix only when it would be noisy on a Swiss/Grid telemetry row. The model id `deepseek-v4-flash-0731` carries the `0731` snapshot date, so `deepseek-v4-flash` is the readable short form.
- **Update the test assertion in `tests/test_ui.py` rather than parametrize it.** `test_strategy_models_are_hard_coded_by_strategy` exists precisely to pin the hardcoded pair; rewriting it to read from `STRATEGY_MODELS` would silently drop the guard. Edit the literal.
- **Do not touch `routing.COST_STRATEGY.model`.** That field is dead at runtime (per the ponytail-cleanup audit in `docs/superpowers/plans/2026-08-21-ponytail-cleanup.md`), and changing it would create a misleading "two sources of truth" story without affecting any inference call.

## Risks / Trade-offs

- [Risk] `deepseek/deepseek-v4-flash-0731` may not be live on OpenRouter the moment the demo runs, or may not be `:free`, breaking the cost-strategy story in the interview. → Mitigation: keep the change scoped to one model id so it can be reverted or pointed at another model with a one-line edit. The error path already renders OpenRouter errors in the UI, so the failure mode is visible.
- [Risk] Future readers see two model ids (`routing.COST_STRATEGY.model` and `STRATEGY_MODELS["cost"]`) and assume the routing module is the source of truth, recreating the ponytail-cleanup confusion. → Mitigation: leave a one-line comment near `STRATEGY_MODELS` explaining that it overrides `RoutingStrategy.model` at the UI call site (only if not already present; do not add if it's already documented inline).
- [Risk] Short label `deepseek-v4-flash` collides visually with other "flash" models if a future strategy adds one. → Mitigation: acceptable for v1; the label map is per-model-id keyed, so collisions are impossible at the data level.

## Migration Plan

No data migration. Deploy is the commit itself: pull, run `uv run pytest tests/test_ui.py` (must pass), start the app with `uv run python app.py`, pick the **Cost** strategy, run a prompt, confirm the response carries the `deepseek/deepseek-v4-flash-0731` model id in the telemetry row.

Rollback is a single revert of the change or a one-line edit restoring `openai/gpt-oss-20b:free`.
