# Technology Stack

**Project:** OpenRouter Production Inference Lab
**Researched:** 2026-08-18
**Overall confidence:** HIGH

## Recommended Stack

### Runtime and App

| Technology | Purpose | Why |
|------------|---------|-----|
| Python 3.12+ | Application runtime | Matches the seed docs and keeps the repo interview-inspectable for a Python-first inference demo. |
| NiceGUI | Local browser UI | Current docs support Python-defined UI elements, async event handlers, background tasks, Tailwind classes, and `ui.run()` for a local browser app. |
| httpx | Async HTTP helper | Keeps direct OpenRouter request bodies visible while supporting streaming, timeouts, and async I/O. |
| OpenRouter Chat Completions API | Inference gateway | Official docs support `/api/v1/chat/completions`, streaming via `stream: true`, provider routing, fallback controls, router metadata, usage, and cache controls. |
| Langfuse Python SDK v4 path | Optional tracing and eval observability | Current SDK docs show `get_client()`, generation/span observations, `usage_details`, `cost_details`, scoring, and `flush()`. |

### Tooling

| Technology | Purpose | Why |
|------------|---------|-----|
| uv | Dependency and command runner | Current uv docs support `uv sync`, `uv run`, lockfiles, and dependency groups. |
| Ruff | Linting and formatting | Current Ruff docs support `ruff check` and `ruff format`; v1 can require `uv run ruff check .`. |
| pytest | Focused tests | Current pytest docs support plain `assert`-based tests and standard `pytest` invocation. |

### Files and Secrets

| Item | Purpose | Why |
|------|---------|-----|
| `.env.example` | Document required and optional credentials | Keeps secrets out of git while making setup visible. |
| `evals/cases.json` | Checked-in deterministic eval cases | Fits the no-database scope and keeps evals cheap and reviewable. |
| Runtime memory | Recent run history | Enough for the local demo; persistence would add non-core complexity. |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| OpenRouter access | Direct HTTPS requests | OpenAI-compatible SDK or OpenRouter SDK | Direct requests expose OpenRouter-specific provider fields and metadata most clearly during an interview. |
| UI | NiceGUI | CLI only | CLI is simpler but weaker for showing streaming, route, fallback, and telemetry evidence in five minutes. |
| UI architecture | Single Python app | Separate JS frontend and API service | Rejected by seed scope and adds unnecessary interview surface area. |
| Observability | Optional Langfuse | Required Langfuse | Missing tracing credentials must not block the core OpenRouter demo. |
| Evals | Deterministic checks | LLM-as-judge first | Deterministic checks are cheaper, repeatable, and inspectable for v1. |

## Sources

- OpenRouter Quickstart: https://openrouter.ai/docs/quickstart
- OpenRouter Chat Completions API: https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request
- OpenRouter Streaming: https://openrouter.ai/docs/api/reference/streaming
- OpenRouter Provider Routing: https://openrouter.ai/docs/guides/routing/provider-selection
- OpenRouter Router Metadata: https://openrouter.ai/docs/guides/features/router-metadata
- NiceGUI docs via Context7 `/zauberzeug/nicegui`
- Langfuse Python SDK docs via Context7 `/langfuse/langfuse-python`
- uv docs via Context7 `/astral-sh/uv`
- Ruff docs: https://docs.astral.sh/ruff/formatter/
- pytest docs: https://docs.pytest.org/en/stable/getting-started.html
