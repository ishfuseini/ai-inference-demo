# Walking Skeleton - OpenRouter Production Inference Lab

**Phase:** 1
**Generated:** 2026-08-18

## Capability Proven End-to-End

A reviewer can run `uv sync`, launch `uv run python app.py`, and see a local NiceGUI setup/status shell that reports OpenRouter and Langfuse credential readiness without live external calls.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Runtime | Python 3.12+ managed by uv | Matches the Python-first interview demo and keeps setup inspectable. |
| UI framework | NiceGUI local browser app | Gives a runnable local shell without a separate frontend or product API layer. |
| Configuration | Exported environment variables through `os.environ` | Implements D-04 and keeps secrets out of the repo. |
| Inference boundary | Direct OpenRouter HTTPS owned by `client.py` in later phases | Preserves the direct OpenRouter requirement while Phase 1 avoids live requests. |
| Observability boundary | Optional Langfuse readiness in config/telemetry modules | Missing Langfuse credentials remain non-blocking and visible. |
| Data layer | No database | Project requirements reject database persistence; runtime history and eval files are local and deferred to later phases. |
| Auth | No authentication | The repo is a local interview lab, not a multi-user product. |
| Deployment target | Local run command | Hosted deployment is out of scope; the skeleton is proven by `uv run python app.py`. |
| Directory layout | `app.py`, `src/openrouter_demo/*`, `tests/`, `evals/` | Gives later phases stable ownership boundaries without reshaping the repo. |

## Stack Touched in Phase 1

- [ ] Project scaffold: `pyproject.toml`, `uv.lock`, pytest, Ruff, runtime dependencies.
- [ ] Routing: local NiceGUI root page through `app.py` and `ui.py`.
- [ ] Database: intentionally absent because the project scope rejects databases.
- [ ] UI: setup/status shell with prompt, strategy, telemetry, history, and eval panel structure in disabled/empty states.
- [ ] Local execution: `uv sync`, `uv run python app.py`, `uv run pytest`, and `uv run ruff check .`.

## Out of Scope (Deferred to Later Slices)

- Live OpenRouter streaming requests.
- Routing strategy execution and fallback behavior.
- Cache/repeat observations.
- Langfuse trace creation.
- Deterministic eval execution and scoring.
- Full interview walkthrough docs.
- High-fidelity UI polish.
- Database, authentication, hosted deployment, or separate API service.

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering its architectural decisions:

- Phase 2: Live streaming OpenRouter request with basic telemetry evidence.
- Phase 3: Routing strategy comparison and reproducible fallback behavior.
- Phase 4: Honest normalized telemetry, repeat/cache observations, and optional Langfuse traces.
- Phase 5: Deterministic eval cases and comparison output.
- Phase 6: Interview walkthrough docs, final quality gates, and failure-tree polish.
