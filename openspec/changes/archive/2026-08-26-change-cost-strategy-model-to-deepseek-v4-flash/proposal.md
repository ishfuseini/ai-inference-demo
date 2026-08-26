## Why

The cost routing strategy currently hardcodes `openai/gpt-oss-20b:free` as the model that gets sent to OpenRouter when the user picks "Cost" in the demo UI. We want to switch that strategy to use `deepseek/deepseek-v4-flash-0731` instead so the live inference path runs against the DeepSeek model without changing any other strategy, capability, or UI affordance.

## What Changes

- Swap the cost-strategy model identifier from `openai/gpt-oss-20b:free` to `deepseek/deepseek-v4-flash-0731` in `STRATEGY_MODELS` in `src/openrouter_demo/ui.py`.
- Replace the matching short display name entry in `STRATEGY_MODEL_SHORT_NAMES` (`"openai/gpt-oss-20b:free": "gpt-oss-20b"`) with `"deepseek/deepseek-v4-flash-0731": "deepseek-v4-flash"`.
- Update `tests/test_ui.py::test_strategy_models_are_hard_coded_by_strategy` to assert the new cost-strategy model value.
- Leave `routing.COST_STRATEGY.model` (`openai/gpt-4o-mini`) and the `intelligence` strategy model untouched.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The set of strategies, the shape of the routing payload, the streaming flow, the telemetry surface, and the UI all stay the same. Only a single string identifier changes. This is a config-value swap, not a behavior change, so the change opts out of specs (`.openspec.yaml` sets `skip_specs: true`).

## Impact

- `src/openrouter_demo/ui.py` — 2 string edits (one in `STRATEGY_MODELS`, one in `STRATEGY_MODEL_SHORT_NAMES`).
- `tests/test_ui.py` — 1 string edit inside `test_strategy_models_are_hard_coded_by_strategy`.
- No API surface change, no dependency change, no env-var change, no migration step. Running `uv run pytest tests/test_ui.py` after the edit must pass without further changes.
- Live runs: the next inference against the cost strategy will hit DeepSeek instead of OpenAI's gpt-oss; OpenRouter returns the provider/router metadata for that model the same way.
