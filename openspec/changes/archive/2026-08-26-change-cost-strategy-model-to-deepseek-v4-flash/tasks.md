## 1. Swap cost-strategy model in `src/openrouter_demo/ui.py`

- [x] 1.1 Change `STRATEGY_MODELS["cost"]` from `"openai/gpt-oss-20b:free"` to `"deepseek/deepseek-v4-flash-0731"` and verify by reading the line back from `src/openrouter_demo/ui.py` (line 52 area) and confirming the new string is present.
- [x] 1.2 Replace the key `"openai/gpt-oss-20b:free"` in `STRATEGY_MODEL_SHORT_NAMES` with `"deepseek/deepseek-v4-flash-0731"` and change its value from `"gpt-oss-20b"` to `"deepseek-v4-flash"`, then verify by reading the dict back from `src/openrouter_demo/ui.py` (line 57 area) and confirming the new key/value pair is present and the old key is gone.

## 2. Update the hardcoded-strategy test in `tests/test_ui.py`

- [x] 2.1 Change the `cost` entry in `test_strategy_models_are_hard_coded_by_strategy` from `"openai/gpt-oss-20b:free"` to `"deepseek/deepseek-v4-flash-0731"` and verify by running `uv run pytest tests/test_ui.py::test_strategy_models_are_hard_coded_by_strategy` and confirming it passes (no other test in the file should need to change).
- [x] 2.2 Run the full UI test file with `uv run pytest tests/test_ui.py` and verify the entire file passes, confirming no other assertion in the file was relying on the old model id.
