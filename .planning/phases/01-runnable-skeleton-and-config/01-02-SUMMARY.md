# Plan 01-02 Summary: Setup Shell and Config

**Status:** Complete

## Built

- Added `pyproject.toml` with Python 3.12+, approved runtime dependencies, dev dependencies, pytest config, Ruff config, and `uv` non-package mode.
- Generated `uv.lock` via `uv sync`.
- Added `app.py` as the reviewer launch entrypoint.
- Added `src/openrouter_demo/config.py` for env-only readiness inspection without returning secret values.
- Added `src/openrouter_demo/ui.py` with a NiceGUI setup/status shell, disabled inference button, missing OpenRouter guidance, and optional Langfuse disabled state.
- Added `.env.example` with empty credential checklist assignments.
- Added setup-focused `README.md`.
- Added config and setup documentation tests in `tests/test_config.py`.

## Verification

- `uv sync` passed.
- `uv run pytest tests/test_config.py tests/test_imports.py tests/test_phase1_guards.py -q` passed after Plan 01-03 tests were added.
- `uv run pytest -q` passed.
- `uv run ruff check .` passed.
- Launch smoke without `OPENROUTER_API_KEY` started NiceGUI on `http://localhost:8080`.

## Notes

No live OpenRouter request, Langfuse trace creation, dotenv parsing, database, or FastAPI product layer was added.
