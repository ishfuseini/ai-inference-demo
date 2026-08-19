# Phase 1: Runnable Skeleton and Config - Research

**Researched:** 2026-08-18
**Domain:** Python 3.12 local NiceGUI skeleton, uv project setup, env configuration, optional Langfuse readiness
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

The following constraints are copied from `.planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md` lines 16-40 and 102-109. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:16-40] [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:102-109]

### Locked Decisions
### Scaffold Shape
- **D-01:** Create the full importable scaffold in Phase 1: `app.py`, `pyproject.toml`, `uv.lock`, `.env.example`, package modules for UI/client/routing/scenarios/telemetry/evals/models/config, `tests/`, and `evals/`. Later phases fill behavior without reshaping the repo.
- **D-02:** Stub modules may exist, but they must be honest and importable. They must not pretend later telemetry, routing, fallback, cache, eval, or live inference behavior exists.

### Configuration And Credentials
- **D-03:** Make `.env.example` immediately useful as the credential checklist, with required `OPENROUTER_API_KEY` and optional Langfuse variables.
- **D-04:** Runtime configuration reads exported environment variables only through `os.environ`; do not add dotenv parsing or a dotenv dependency in Phase 1.
- **D-05:** Missing `OPENROUTER_API_KEY` launches a real NiceGUI setup/status shell and does not attempt any live request.
- **D-06:** Missing Langfuse credentials are visibly shown as optional/disabled and do not block launch.
- **D-07:** `.env.example` must contain variable names and comments only, never secret-like values.

### App Shell
- **D-08:** The first NiceGUI screen should structurally resemble the intended inference operations console, with setup state and disabled/empty panels rather than fake inference behavior.
- **D-09:** Visual polish is not a Phase 1 priority because the user plans to run `impeccable` afterward for UI touches. Keep the shell clean and understandable, but avoid spending Phase 1 on high-fidelity styling.

### Documentation
- **D-10:** Add minimal README setup documentation now: install, env vars, launch, and clearly marked future demo capabilities. The full interview walkthrough remains Phase 6.

### Dependencies And Verification
- **D-11:** Include the whole planned dependency stack now: NiceGUI, httpx, Langfuse SDK, pytest, Ruff, and Python 3.12+ via `uv`.
- **D-12:** Phase 1 verification should prove setup and imports only: `uv sync`, config/import/env behavior tests, Ruff, and launch smoke check without any live OpenRouter request.

### the agent's Discretion
- The implementer may choose simple names and minimal stub contents that match Python project conventions, as long as the scaffold boundaries above remain clear.
- The implementer may keep README wording concise and setup-focused; final demo storytelling belongs in Phase 6.

### Deferred Ideas (OUT OF SCOPE)
- Live OpenRouter streaming request - Phase 2.
- Routing and reproducible fallback behavior - Phase 3.
- Honest normalized telemetry, repeat/cache observations, and optional Langfuse traces - Phase 4.
- Deterministic eval command and comparison output - Phase 5.
- Full interview README/walkthrough and final quality-gate polish - Phase 6.
</user_constraints>

## Summary

Phase 1 should create a runnable, importable Python skeleton and stop there. The phase must prove the reviewer can run `uv sync` and `uv run python app.py`, see a real NiceGUI setup/status shell, and understand credential readiness without any live OpenRouter call. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:9-10, quote: "`uv sync` and `uv run python app.py`"] [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:22-24, quote: "`os.environ`; do not add dotenv parsing or a dotenv dependency in Phase 1"; "Missing `OPENROUTER_API_KEY` launches a real NiceGUI setup/status shell and does not attempt any live request."]

The full dependency stack should be declared now because D-11 locks NiceGUI, httpx, Langfuse SDK, pytest, Ruff, and Python 3.12+ via uv. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:35-36, quote: "NiceGUI, httpx, Langfuse SDK, pytest, Ruff, and Python 3.12+ via `uv`"] The implementation should keep all later behavior honest by using importable stubs that do not simulate telemetry, routing, fallback, cache, eval, or live inference. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:18-18]

**Primary recommendation:** Use a `src/openrouter_demo` package with a thin `app.py`, env-only config inspection, a non-live NiceGUI operations-console shell, `.env.example`, README setup docs, `uv.lock`, Ruff config, and focused pytest tests for import/config behavior. [VERIFIED: docs/PRD.md:220-250, quote: "`app.py`"; "`src/`"; "`openrouter_demo/`"; "`config.py`"; "`ui.py`"; "`tests/`"] [VERIFIED: docs/specs/acceptance-criteria.md:69-85]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Dependency installation and lockfile | Build / Tooling | Python package | `uv sync`, `pyproject.toml`, and `uv.lock` own reproducible setup. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:16-17, quote: "`pyproject.toml`, `uv.lock`"] |
| Env credential inspection | Python package | NiceGUI UI | `src/openrouter_demo/config.py` should own environment inspection and expose setup state to the UI. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:87-89, quote: "`src/openrouter_demo/config.py` should own environment inspection and expose setup state to the UI."] |
| Missing credential guidance | NiceGUI UI | Python config | Missing `OPENROUTER_API_KEY` must launch setup/status UI and avoid live requests. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:23-24] |
| Optional Langfuse readiness | Python config | NiceGUI UI | Langfuse credentials should be detected separately and shown as optional/disabled when absent. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:24-24] |
| Importable future boundaries | Python package | Tests | The required layout separates UI, client, routing, scenarios, telemetry, evals, and typed models. [VERIFIED: .planning/REQUIREMENTS.md:15-15, quote: "UI, client, routing, scenarios, telemetry, evals, and typed models"] |
| Launch shell | NiceGUI UI | App entrypoint | `app.py` starts the NiceGUI app, while `ui.py` renders the setup/status shell. [VERIFIED: docs/PRD.md:253-261, quote: "`app.py`"; "`ui.py`"] |
| Non-live verification | Tests / Tooling | NiceGUI UI | D-12 limits verification to setup/import/env/Ruff/launch smoke without live OpenRouter requests. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:35-36] |

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SETUP-01 | Reviewer can install project dependencies with `uv sync`. [VERIFIED: .planning/REQUIREMENTS.md:10-10] | Use uv project metadata and lockfile; verify with `uv sync`. [CITED: /astral-sh/uv via Context7] |
| SETUP-02 | Reviewer can launch the NiceGUI app with `uv run python app.py`. [VERIFIED: .planning/REQUIREMENTS.md:11-11] | Thin `app.py` imports config/UI and calls NiceGUI `ui.run()`. [CITED: /zauberzeug/nicegui via Context7] |
| SETUP-03 | Reviewer can configure the required `OPENROUTER_API_KEY` without committing secrets. [VERIFIED: .planning/REQUIREMENTS.md:12-12] | Use `.env.example`, `.gitignore` ignores `.env`, and runtime reads `os.environ`. [VERIFIED: .gitignore:126-128, quote: "`.env`"; "`.venv`"] |
| SETUP-04 | Reviewer can omit Langfuse credentials and still run the core inference demo. [VERIFIED: .planning/REQUIREMENTS.md:13-13] | Config model should report Langfuse disabled when its env vars are incomplete. [CITED: /langfuse/langfuse-python via Context7] |
| SETUP-05 | App shows clear setup guidance when the required OpenRouter credential is missing. [VERIFIED: .planning/REQUIREMENTS.md:14-14] | NiceGUI shell should render setup status and disabled/empty panels without live request attempts. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:23-29] |
| SETUP-06 | Repository includes a Python package layout that separates UI, client, routing, scenarios, telemetry, evals, and typed models. [VERIFIED: .planning/REQUIREMENTS.md:15-15] | Create `src/openrouter_demo` modules now as honest importable stubs. [VERIFIED: docs/PRD.md:228-250] |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- Use Python 3.12+, NiceGUI, httpx, Langfuse Python SDK, uv, Ruff, and pytest. [VERIFIED: AGENTS.md:13-21, quote: "Python 3.12+, NiceGUI, httpx, Langfuse Python SDK, uv, Ruff, pytest"]
- Use direct OpenRouter Chat Completions over HTTPS in later inference phases; Phase 1 must not hide future OpenRouter-specific routing/metadata behind another router. [VERIFIED: AGENTS.md:16-16]
- Missing Langfuse credentials must visibly disable tracing without blocking inference. [VERIFIED: AGENTS.md:17-17]
- Use environment variables and `.env.example`; never commit API keys. [VERIFIED: AGENTS.md:18-18]
- Default prompts and eval cases must stay small and bounded. [VERIFIED: AGENTS.md:19-19]
- Token, cost, provider, router, and cache fields must distinguish unavailable values from zero values. [VERIFIED: AGENTS.md:20-20]
- NiceGUI is the local browser UI; FastAPI is only an internal NiceGUI implementation detail. [VERIFIED: AGENTS.md:21-21]
- Keep Phase 1 surgical: no features beyond the requested skeleton, no speculative abstractions, and no unrelated refactors. [VERIFIED: AGENTS.md:40-66]
- Use goal-driven verification: tests and commands should prove setup/import/env behavior. [VERIFIED: AGENTS.md:68-84]

## Verified Discrete Values

| Value Type | Verbatim Values | Source |
|------------|-----------------|--------|
| Required commands | "`uv sync`"; "`uv run python app.py`" | [VERIFIED: docs/specs/quickstart.md:15-17] [VERIFIED: docs/specs/quickstart.md:41-43] |
| Credential env vars | "`OPENROUTER_API_KEY`"; "`LANGFUSE_PUBLIC_KEY`"; "`LANGFUSE_SECRET_KEY`"; "`LANGFUSE_BASE_URL`" | [VERIFIED: docs/specs/quickstart.md:25-31] |
| Package layout paths | "`app.py`"; "`pyproject.toml`"; "`uv.lock`"; "`.env.example`"; "`src/openrouter_demo/`"; "`tests/`"; "`evals/`" | [VERIFIED: docs/PRD.md:220-250] |
| Module paths | "`client.py`"; "`config.py`"; "`evals.py`"; "`models.py`"; "`routing.py`"; "`scenarios.py`"; "`telemetry.py`"; "`ui.py`" | [VERIFIED: docs/PRD.md:230-238] |
| Screen labels | "`OpenRouter Production Inference Lab`"; "`Route, observe, recover, and evaluate model calls.`"; "`Prompt`"; "`Sample prompt`"; "`Run Inference`" | [VERIFIED: docs/ux/screen-spec.md:27-82] |
| Strategy labels | "`Default`"; "`Cost optimized`"; "`Latency optimized`"; "`Custom`"; "`Simulate primary route failure`" | [VERIFIED: docs/ux/screen-spec.md:108-170] |
| Config gates | "`nyquist_validation`: true"; "`security_enforcement`: true"; "`security_asvs_level`: 1" | [VERIFIED: .planning/config.json:20-49] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ project target; local Python is 3.14.5 | Runtime | Project constraints require Python 3.12+ for an inspectable Python-first demo. [VERIFIED: AGENTS.md:15-15] [VERIFIED: local `python3 --version`, 2026-08-18] |
| `nicegui` [WARNING: flagged as suspicious by package-legitimacy seam - verify before using.] | 3.16.0, uploaded 2026-08-12T15:18:28Z | Local browser UI | Context7 identifies `/zauberzeug/nicegui`; docs support `ui.run()`, async handlers, and background tasks for later streaming. [CITED: /zauberzeug/nicegui via Context7] [VERIFIED: PyPI JSON, 2026-08-18] |
| `httpx` [WARNING: flagged as suspicious by package-legitimacy seam - verify before using.] | 0.28.1, uploaded 2024-12-06T15:37:21Z | Async HTTP helper for later direct OpenRouter calls | Context7 identifies `/encode/httpx`; docs support `AsyncClient.stream()` and timeout configuration. [CITED: /encode/httpx via Context7] [VERIFIED: PyPI JSON, 2026-08-18] |
| `langfuse` [WARNING: flagged as suspicious by package-legitimacy seam - verify before using.] | 4.14.4, uploaded 2026-08-11T17:03:20Z | Optional tracing dependency | Context7 identifies `/langfuse/langfuse-python`; docs support env vars, `get_client()`, observations, usage/cost details, scores, and `flush()`. [CITED: /langfuse/langfuse-python via Context7] [VERIFIED: PyPI JSON, 2026-08-18] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` [WARNING: flagged as suspicious by package-legitimacy seam - verify before using.] | 9.1.1, uploaded 2026-06-19T10:58:31Z | Test runner | Use for config/env/importability tests in Phase 1 and later behavior tests. [CITED: /pytest-dev/pytest via Context7] [VERIFIED: PyPI JSON, 2026-08-18] |
| `ruff` [WARNING: flagged as suspicious by package-legitimacy seam - verify before using.] | 0.16.3, uploaded 2026-08-13T15:16:27Z | Lint and format | Use `ruff check` as the non-mutating phase gate; optionally use `ruff format --check`. [CITED: /astral-sh/ruff via Context7] [VERIFIED: PyPI JSON, 2026-08-18] |
| `uv` [WARNING: flagged as suspicious by package-legitimacy seam - verify before using if installing/upgrading.] | PyPI latest 0.12.5, uploaded 2026-08-14T19:55:51Z; local installed 0.5.9 | Project manager and command runner | Use existing local uv for `uv sync` and `uv run`; planner may add an upgrade note if lock generation fails. [CITED: /astral-sh/uv via Context7] [VERIFIED: local `uv --version`, 2026-08-18] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Env-only config through `os.environ` | dotenv parsing | Rejected by D-04 for Phase 1 even though uv docs mention env-file support. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:22-22] [CITED: https://docs.astral.sh/uv/concepts/configuration-files/] |
| Direct NiceGUI shell | Separate FastAPI service | Rejected by project constraints; FastAPI is an internal NiceGUI detail. [VERIFIED: AGENTS.md:21-21] |
| Importable honest stubs | Fake scenario output | Rejected by D-02 because stubs must not pretend later behavior exists. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:18-18] |
| Required Langfuse startup | Optional tracing status | Rejected by SETUP-04 and D-06; missing Langfuse credentials must not block launch. [VERIFIED: .planning/REQUIREMENTS.md:13-13] [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:24-24] |

**Installation:**
```bash
uv add nicegui httpx langfuse
uv add --dev pytest ruff
uv sync
```

**Reviewer commands:**
```bash
uv sync
uv run python app.py
uv run pytest
uv run ruff check .
```

**Version verification:** Versions above were checked with `python3 -m pip index versions <package>` and PyPI JSON on 2026-08-18. [VERIFIED: PyPI registry query, 2026-08-18]

## Package Legitimacy Audit

> The GSD package-legitimacy seam returned `SUS` for every checked PyPI package, mostly because weekly downloads were unavailable to the seam and recent releases tripped the "too-new" signal. Because the dependencies are locked by D-11, keep them but require a human verification checkpoint before install. [VERIFIED: package-legitimacy seam, 2026-08-18]

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `nicegui` | PyPI | Latest upload 2026-08-12 | unknown to seam | https://nicegui.io | SUS: too-new, unknown-downloads | Flagged - planner must add checkpoint |
| `httpx` | PyPI | Latest upload 2024-12-06 | unknown to seam | https://github.com/encode/httpx | SUS: unknown-downloads | Flagged - planner must add checkpoint |
| `langfuse` | PyPI | Latest upload 2026-08-11 | unknown to seam | none returned by seam | SUS: too-new, unknown-downloads, no-repository | Flagged - planner must add checkpoint |
| `pytest` | PyPI | Latest upload 2026-06-19 | unknown to seam | https://github.com/pytest-dev/pytest | SUS: unknown-downloads | Flagged - planner must add checkpoint |
| `ruff` | PyPI | Latest upload 2026-08-13 | unknown to seam | https://docs.astral.sh/ruff | SUS: too-new, unknown-downloads | Flagged - planner must add checkpoint |
| `uv` | PyPI / local CLI | Latest upload 2026-08-14; local install 0.5.9 | unknown to seam | https://pypi.org/project/uv/ | SUS: too-new, unknown-downloads | Flagged only if planner installs/upgrades uv |

**Packages removed due to [SLOP] verdict:** none. [VERIFIED: package-legitimacy seam, 2026-08-18]
**Packages flagged as suspicious [SUS]:** `nicegui`, `httpx`, `langfuse`, `pytest`, `ruff`, `uv`. [VERIFIED: package-legitimacy seam, 2026-08-18]

## Architecture Patterns

### System Architecture Diagram

```text
Reviewer shell
  |
  | uv sync
  v
pyproject.toml + uv.lock
  |
  | uv run python app.py
  v
app.py
  |
  | load setup state
  v
src/openrouter_demo/config.py
  |
  | required key present?
  +-- no  -> src/openrouter_demo/ui.py -> setup guidance shell -> no live request
  |
  +-- yes -> src/openrouter_demo/ui.py -> operations-console shell with future panels disabled/empty
                                  |
                                  +-> client/routing/scenarios/telemetry/evals/models import stubs
                                  |
                                  +-> Langfuse status: enabled only if optional env vars are present
```

### Recommended Project Structure

```text
app.py
pyproject.toml
uv.lock
.env.example
README.md
src/
└── openrouter_demo/
    ├── __init__.py
    ├── client.py
    ├── config.py
    ├── evals.py
    ├── models.py
    ├── routing.py
    ├── scenarios.py
    ├── telemetry.py
    └── ui.py
evals/
└── cases.json
tests/
├── test_config.py
└── test_imports.py
```

This structure is a Phase 1 subset of the PRD layout and satisfies D-01 without creating fake later behavior. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:17-18] [VERIFIED: docs/PRD.md:220-250]

### Pattern 1: Env-Only Configuration Object

**What:** Centralize env inspection in `config.py`; return readiness booleans and missing-key names, not secret values. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:21-25]
**When to use:** Use for app startup, setup UI, and tests. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:87-90]
**Example:**
```python
# Source: Phase 1 context and Langfuse docs via Context7.
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    openrouter_ready: bool
    langfuse_ready: bool
    missing_required: tuple[str, ...]


def load_config(environ: dict[str, str] | None = None) -> AppConfig:
    source = os.environ if environ is None else environ
    openrouter_ready = bool(source.get("OPENROUTER_API_KEY"))
    langfuse_ready = all(
        source.get(name)
        for name in (
            "LANGFUSE_PUBLIC_KEY",
            "LANGFUSE_SECRET_KEY",
            "LANGFUSE_BASE_URL",
        )
    )
    return AppConfig(
        openrouter_ready=openrouter_ready,
        langfuse_ready=langfuse_ready,
        missing_required=() if openrouter_ready else ("OPENROUTER_API_KEY",),
    )
```

### Pattern 2: Thin NiceGUI Entrypoint

**What:** Keep `app.py` as startup glue and keep UI composition in `ui.py`. [VERIFIED: docs/PRD.md:253-261]
**When to use:** Use for SETUP-02 launch verification. [VERIFIED: .planning/REQUIREMENTS.md:11-11]
**Example:**
```python
# Source: NiceGUI docs via Context7 and PRD app.py boundary.
from nicegui import ui

from openrouter_demo.config import load_config
from openrouter_demo.ui import build_app


build_app(load_config())

ui.run(title="OpenRouter Production Inference Lab")
```

### Pattern 3: Honest Importable Stubs

**What:** Define module-level placeholders and simple types that import cleanly but raise clear "not implemented in Phase 1" errors only if later behavior is called. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:17-18]
**When to use:** Use in `client.py`, `routing.py`, `scenarios.py`, `telemetry.py`, `evals.py`, and `models.py` until later phases add behavior. [VERIFIED: docs/PRD.md:230-238]
**Example:**
```python
# Source: Phase 1 D-02 requires honest, importable stubs.
class PhaseNotImplementedError(RuntimeError):
    pass


def stream_chat_completion(*_: object, **__: object) -> None:
    raise PhaseNotImplementedError("Live OpenRouter streaming is planned for Phase 2.")
```

### Anti-Patterns to Avoid

- **dotenv parsing in Phase 1:** D-04 explicitly requires exported env variables through `os.environ`; do not add `python-dotenv`. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:22-22]
- **Live OpenRouter smoke tests:** D-12 limits Phase 1 verification to setup/import/env/Ruff/launch smoke without live OpenRouter requests. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:35-36]
- **Fake telemetry/routing/cache/eval panels:** D-02 forbids stubs that pretend later behavior exists. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:18-18]
- **Making Langfuse required:** SETUP-04 and D-06 require Langfuse to be optional. [VERIFIED: .planning/REQUIREMENTS.md:13-13] [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:24-24]
- **Presenting FastAPI as a layer:** Project constraints say NiceGUI is the local UI and FastAPI is only an internal implementation detail. [VERIFIED: AGENTS.md:21-21]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Project environment and lockfile | Custom install script | uv project metadata and `uv.lock` | uv docs support `uv sync`, `uv lock`, dependency groups, and `uv run`. [CITED: /astral-sh/uv via Context7] |
| Browser UI shell | Custom HTTP server or JS frontend | NiceGUI | Project constraints lock NiceGUI and reject a separate frontend/backend service. [VERIFIED: AGENTS.md:21-21] |
| HTTP streaming foundation for later phases | Raw sockets or ad hoc async wrappers | httpx `AsyncClient.stream()` | HTTPX docs support async streaming and timeout configuration. [CITED: /encode/httpx via Context7] |
| Tracing SDK surface | Homemade Langfuse HTTP calls | Langfuse Python SDK | Langfuse docs support env vars, observations, usage/cost details, scoring, and flush. [CITED: /langfuse/langfuse-python via Context7] |
| Test runner | Custom shell assertions | pytest | pytest docs support plain assert-based test discovery under `test_*.py`/`*_test.py`. [CITED: /pytest-dev/pytest via Context7] |
| Lint/format gate | Multiple lint tools | Ruff | Ruff docs support `ruff check` and `ruff format` under one tool. [CITED: /astral-sh/ruff via Context7] |

**Key insight:** Phase 1 is setup credibility work; hand-rolled infrastructure weakens the interview artifact because it adds code that does not demonstrate OpenRouter inference behavior. [VERIFIED: AGENTS.md:7-11]

## Common Pitfalls

### Pitfall 1: Accidentally making `.env` loading part of the product
**What goes wrong:** The app depends on a local `.env` parser or undocumented `uv --env-file` behavior. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:22-22]
**Why it happens:** uv supports env-file loading, but D-04 narrows Phase 1 to exported env variables only. [CITED: https://docs.astral.sh/uv/concepts/configuration-files/] [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:22-22]
**How to avoid:** Test `load_config()` by injecting dictionaries and by clearing env vars; do not install dotenv. [ASSUMED]
**Warning signs:** `python-dotenv` in dependencies or app behavior that differs between `uv run python app.py` and exported-shell runs. [ASSUMED]

### Pitfall 2: Treating missing OpenRouter credentials as an app crash
**What goes wrong:** `uv run python app.py` exits before showing the NiceGUI page. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:23-23]
**Why it happens:** Config validation is performed as a hard startup exception. [ASSUMED]
**How to avoid:** Model setup readiness separately from launch readiness; only future live calls require `OPENROUTER_API_KEY`. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:23-24]
**Warning signs:** Tests assert process failure when `OPENROUTER_API_KEY` is missing. [ASSUMED]

### Pitfall 3: Importable stubs that lie
**What goes wrong:** Disabled panels display fake model/provider/cost/cache values. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:18-18]
**Why it happens:** The skeleton tries to look more complete than Phase 1 allows. [ASSUMED]
**How to avoid:** Use empty states like "not wired yet" and future panel shells without generated inference data. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:28-29]
**Warning signs:** Hard-coded telemetry values, fake cache hits, or fake Langfuse trace IDs. [VERIFIED: AGENTS.md:20-20]

### Pitfall 4: Over-polishing the first shell
**What goes wrong:** Phase 1 spends effort on final visual design instead of setup reliability. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:29-29]
**Why it happens:** The eventual UI is important, but the user plans to run `impeccable` after Phase 1. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:97-98]
**How to avoid:** Build a clean operations-console structure using labels from `docs/ux/screen-spec.md`; defer high-fidelity styling. [VERIFIED: docs/ux/screen-spec.md:13-21]
**Warning signs:** Large CSS/theming work before `uv sync`, imports, and launch are proven. [ASSUMED]

### Pitfall 5: Using package latests without a human checkpoint
**What goes wrong:** The planner installs packages that the legitimacy gate flagged as `SUS`. [VERIFIED: package-legitimacy seam, 2026-08-18]
**Why it happens:** The seam cannot see download counts and flags recent releases. [VERIFIED: package-legitimacy seam, 2026-08-18]
**How to avoid:** Add a `checkpoint:human-verify` task before installing flagged packages, then generate `uv.lock`. [VERIFIED: package-legitimacy protocol in prompt]
**Warning signs:** A plan step runs `uv add ...` with no preceding checkpoint. [ASSUMED]

## Code Examples

Verified patterns from official sources and phase sources:

### pyproject Skeleton
```toml
# Source: uv docs via Context7, package versions verified from PyPI on 2026-08-18.
[project]
name = "openrouter-production-inference-lab"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "nicegui>=3.16.0",
  "httpx>=0.28.1",
  "langfuse>=4.14.4",
]

[dependency-groups]
dev = [
  "pytest>=9.1.1",
  "ruff>=0.16.3",
]

[tool.ruff]
target-version = "py312"
line-length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### Config Test Pattern
```python
# Source: pytest docs via Context7 and Phase 1 config requirements.
from openrouter_demo.config import load_config


def test_missing_openrouter_key_keeps_app_launchable() -> None:
    config = load_config({})

    assert not config.openrouter_ready
    assert config.missing_required == ("OPENROUTER_API_KEY",)


def test_langfuse_is_optional_with_openrouter_key_only() -> None:
    config = load_config({"OPENROUTER_API_KEY": "test-key"})

    assert config.openrouter_ready
    assert not config.langfuse_ready
```

### NiceGUI Shell Pattern
```python
# Source: NiceGUI docs via Context7 and screen-spec labels.
from nicegui import ui

from openrouter_demo.config import AppConfig


def build_app(config: AppConfig) -> None:
    ui.label("OpenRouter Production Inference Lab")
    ui.label("Route, observe, recover, and evaluate model calls.")

    if not config.openrouter_ready:
        ui.label("Set OPENROUTER_API_KEY in your environment before running inference.")

    trace_status = "enabled" if config.langfuse_ready else "disabled"
    ui.label(f"Langfuse tracing: {trace_status}")

    ui.textarea(label="Prompt")
    ui.button("Run Inference", on_click=None).disable()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Poetry/Pipenv setup for small Python demos | uv project metadata with `uv sync` and `uv run` | Current uv docs queried 2026-08-18 | Planner should create `pyproject.toml` and `uv.lock`, not a bespoke virtualenv script. [CITED: /astral-sh/uv via Context7] |
| Separate frontend for browser UI | NiceGUI Python-defined local UI | Project locked before Phase 1 | Planner should avoid JS build tooling. [VERIFIED: AGENTS.md:21-21] |
| Required tracing service at startup | Optional Langfuse readiness status | Project locked before Phase 1 | Planner should include Langfuse dependency but not block launch on missing Langfuse env vars. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:24-24] |
| dotenv application dependency | Exported env vars through `os.environ` | Phase 1 context locked 2026-08-18 | Planner should not add `python-dotenv`. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:22-22] |

**Deprecated/outdated:**
- Treating FastAPI as a separate product layer is out of scope for this repo. [VERIFIED: AGENTS.md:21-21]
- Making Langfuse mandatory is out of scope for setup and runtime launch. [VERIFIED: .planning/REQUIREMENTS.md:13-13]
- Claiming metadata, cost, cache, provider, or trace data before live behavior exists is out of scope for Phase 1. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:18-18]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Tests can inject dictionaries into `load_config()` rather than mutating process env directly. | Common Pitfalls / Code Examples | Low: planner may instead use `monkeypatch.setenv`, but must still test same behavior. |
| A2 | Warning signs such as hard-coded telemetry values and fake trace IDs are sufficient review heuristics for Phase 1. | Common Pitfalls | Medium: planner may need more explicit UI assertions if implementation gets larger. |
| A3 | Launch smoke check can be non-live and bounded by starting then stopping the NiceGUI process. | Validation Architecture | Medium: NiceGUI process handling may need a subprocess timeout or manual check. |

## Open Questions (RESOLVED)

1. **Should the planner pin exact package versions or allow compatible ranges?**
   - What we know: Current PyPI latests are listed above, but every package was flagged `SUS` by the legitimacy seam. [VERIFIED: PyPI JSON, 2026-08-18] [VERIFIED: package-legitimacy seam, 2026-08-18]
   - RESOLVED: Use conservative compatible lower bounds in `pyproject.toml` after the human package legitimacy checkpoint, then rely on `uv.lock` for exact resolution.
   - Planner impact: Plan 01-02 must write lower-bound dependency specifiers for `nicegui`, `httpx`, `langfuse`, `pytest`, and `ruff`; the generated `uv.lock` provides the exact installed versions.

2. **Should Phase 1 include `evals/cases.json` as an empty file or a small placeholder?**
   - What we know: D-01 says create `evals/`, and deferred ideas place deterministic eval command/output in Phase 5. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:17-18] [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:105-109]
   - RESOLVED: Create an honest `evals/` placeholder such as `evals/.gitkeep` or `evals/README.md`; do not create fake `evals/cases.json` or fake eval cases in Phase 1.
   - Planner impact: Plan 01-03 uses `evals/.gitkeep` so the directory exists without implying eval cases or eval execution are available.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Runtime and uv project | yes | 3.14.5 local; project target `>=3.12` | Install Python 3.12+ if missing. [VERIFIED: local `python3 --version`, 2026-08-18] |
| uv | `uv sync`, `uv run` | yes | 0.5.9 local; PyPI latest 0.12.5 | Upgrade uv if lock generation or dependency groups fail. [VERIFIED: local `uv --version`, 2026-08-18] [VERIFIED: PyPI JSON, 2026-08-18] |
| pip / PyPI access | Registry verification | yes | pip command available through Python | Use PyPI JSON if `pip index` output changes. [VERIFIED: local command check, 2026-08-18] |
| Ruff executable | Quality gate after sync | no global executable detected | Not installed globally | Use `uv run ruff check .` after `uv sync`. [VERIFIED: local command check, 2026-08-18] |
| pytest executable | Test gate after sync | no global executable detected | Not installed globally | Use `uv run pytest` after `uv sync`. [VERIFIED: local command check, 2026-08-18] |
| OpenRouter API key | Future live inference; setup status now | missing in current shell | secret value not read | App must still launch and show setup guidance. [VERIFIED: local env presence check, 2026-08-18] |
| Langfuse env vars | Optional tracing status | missing in current shell | secret values not read | App must show tracing disabled. [VERIFIED: local env presence check, 2026-08-18] |

**Missing dependencies with no fallback:**
- None for Phase 1 skeleton planning; missing OpenRouter credentials are an expected setup state, not a launch blocker. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:23-24]

**Missing dependencies with fallback:**
- Global Ruff/pytest are missing, but project-local `uv run ruff check .` and `uv run pytest` are the intended path after `uv sync`. [VERIFIED: docs/specs/quickstart.md:91-99]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 [VERIFIED: PyPI JSON, 2026-08-18] |
| Config file | none currently; add `[tool.pytest.ini_options]` to `pyproject.toml` in Wave 0. [VERIFIED: test config scan, 2026-08-18] |
| Quick run command | `uv run pytest tests/test_config.py tests/test_imports.py -q` [ASSUMED] |
| Full suite command | `uv run pytest` [VERIFIED: docs/specs/quickstart.md:91-99, quote: "`uv run pytest`"] |
| Lint command | `uv run ruff check .` [VERIFIED: docs/specs/acceptance-criteria.md:82-83, quote: "`uv run ruff check .`"] |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| SETUP-01 | `uv sync` installs dependencies | install smoke | `uv sync` | no `pyproject.toml` yet - Wave 0 [VERIFIED: .planning/REQUIREMENTS.md:10-10] |
| SETUP-02 | `uv run python app.py` launches NiceGUI | launch smoke | `timeout 10 uv run python app.py` or manual local launch check | no `app.py` yet - Wave 0 [ASSUMED] |
| SETUP-03 | Required OpenRouter key is documented and read from env without committing secrets | unit | `uv run pytest tests/test_config.py -q` | no tests yet - Wave 0 [VERIFIED: .planning/REQUIREMENTS.md:12-12] |
| SETUP-04 | Missing Langfuse credentials keep app runnable | unit | `uv run pytest tests/test_config.py -q` | no tests yet - Wave 0 [VERIFIED: .planning/REQUIREMENTS.md:13-13] |
| SETUP-05 | Missing OpenRouter key shows setup guidance and does not attempt a live request | smoke/unit | `uv run pytest tests/test_config.py tests/test_imports.py -q` plus launch smoke | no tests yet - Wave 0 [VERIFIED: .planning/REQUIREMENTS.md:14-14] |
| SETUP-06 | Package modules import separately | unit | `uv run pytest tests/test_imports.py -q` | no tests yet - Wave 0 [VERIFIED: .planning/REQUIREMENTS.md:15-15] |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_config.py tests/test_imports.py -q` and `uv run ruff check .` when files exist. [ASSUMED]
- **Per wave merge:** `uv run pytest` and `uv run ruff check .`. [VERIFIED: docs/specs/quickstart.md:91-99]
- **Phase gate:** `uv sync`, `uv run pytest`, `uv run ruff check .`, and a launch smoke check without a live OpenRouter request. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:35-36]

### Wave 0 Gaps

- [ ] `pyproject.toml` - project metadata, dependencies, dev dependency group, Ruff/pytest config. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:17-17]
- [ ] `uv.lock` - generated after human package verification and `uv sync`. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:17-17]
- [ ] `app.py` - thin launch entrypoint. [VERIFIED: docs/PRD.md:253-255]
- [ ] `src/openrouter_demo/config.py` - env inspection. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:87-88]
- [ ] `src/openrouter_demo/ui.py` - setup/status shell. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:88-89]
- [ ] `tests/test_config.py` - missing/present credential behavior. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:89-90]
- [ ] `tests/test_imports.py` - all scaffold modules import cleanly. [VERIFIED: .planning/REQUIREMENTS.md:15-15]

## Security Domain

Security enforcement is enabled at ASVS level 1. [VERIFIED: .planning/config.json:47-49, quote: "`security_enforcement`: true"; "`security_asvs_level`: 1"] OWASP ASVS 5.0.0 is the current stable ASVS version according to the OWASP project page queried on 2026-08-18. [CITED: https://owasp.org/www-project-application-security-verification-standard/]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V1 Encoding and Sanitization | yes | Treat prompt text and setup strings as untrusted display data; rely on NiceGUI escaping/default components and avoid raw HTML for user input. [CITED: OWASP ASVS 5.0 index] [ASSUMED] |
| V2 Validation and Business Logic | yes | Validate setup readiness through explicit config state and tests; do not permit live inference without required OpenRouter key in later phases. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:23-24] |
| V3 Web Frontend Security | limited | Local NiceGUI shell only; avoid custom browser security mechanisms in Phase 1. [VERIFIED: AGENTS.md:21-21] [ASSUMED] |
| V4 API and Web Service | future | No live OpenRouter API call in Phase 1; reserve API request validation for Phase 2. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:105-105] |
| V5 File Handling | no | Phase 1 has no upload/download feature. [VERIFIED: .planning/REQUIREMENTS.md:8-15] |
| V6 Authentication | no | Project out of scope excludes authentication. [VERIFIED: .planning/REQUIREMENTS.md:74-80, quote: "Authentication | Local interview demo does not need users or accounts."] |
| V7 Session Management | no | No user accounts or sessions are in Phase 1 scope. [VERIFIED: .planning/REQUIREMENTS.md:74-80] |
| V8 Authorization | no | No roles, users, or tenant boundaries are in Phase 1 scope. [VERIFIED: .planning/REQUIREMENTS.md:74-80] |
| V14 Configuration | yes | Keep secrets in environment variables and `.env.example`; `.gitignore` already ignores `.env`. [VERIFIED: AGENTS.md:18-18] [VERIFIED: .gitignore:126-128] |

### Known Threat Patterns for Python Local UI Setup

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Secret leakage through committed files | Information Disclosure | `.env.example` contains names/comments only, `.env` stays ignored, tests should scan `.env.example` for placeholder-only values. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:25-25] [VERIFIED: .gitignore:126-128] |
| Live request attempt without required key | Information Disclosure / Reliability | Missing `OPENROUTER_API_KEY` launches setup UI and does not attempt a live request. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:23-23] |
| Dependency confusion or slopsquatted package | Tampering | Use package-legitimacy checkpoint and correct PyPI registry verification before `uv add`. [VERIFIED: package-legitimacy seam, 2026-08-18] |
| Displaying untrusted prompt text as HTML | Cross-site scripting / Tampering | Use NiceGUI text components and avoid raw HTML injection for user-provided prompt content. [ASSUMED] |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md` - locked Phase 1 scope, decisions, deferred ideas, and code context. [VERIFIED: local file read, 2026-08-18]
- `.planning/REQUIREMENTS.md` - SETUP-01 through SETUP-06 and project traceability. [VERIFIED: local file read, 2026-08-18]
- `AGENTS.md` - project constraints and workflow expectations. [VERIFIED: local file read, 2026-08-18]
- `docs/specs/quickstart.md` and `docs/specs/acceptance-criteria.md` - setup commands and repository acceptance criteria. [VERIFIED: local file read, 2026-08-18]
- PyPI registry JSON and `pip index versions` - current package versions and upload dates. [VERIFIED: PyPI registry query, 2026-08-18]

### Secondary (MEDIUM confidence)
- Context7 `/zauberzeug/nicegui` - `ui.run()`, async rules, background tasks. [CITED: /zauberzeug/nicegui via Context7]
- Context7 `/astral-sh/uv` - project management, dependency groups, `uv sync`, `uv run`. [CITED: /astral-sh/uv via Context7]
- Context7 `/langfuse/langfuse-python` - env vars, `get_client()`, observations, usage/cost details, scoring, flush. [CITED: /langfuse/langfuse-python via Context7]
- Context7 `/encode/httpx` - async streaming and timeout patterns. [CITED: /encode/httpx via Context7]
- Context7 `/pytest-dev/pytest` - test discovery and invocation. [CITED: /pytest-dev/pytest via Context7]
- Context7 `/astral-sh/ruff` - `ruff check`, `ruff format`, pyproject config. [CITED: /astral-sh/ruff via Context7]
- OpenRouter Quickstart and API authentication docs - bearer token and direct HTTP endpoint context for future phases. [CITED: https://openrouter.ai/docs/quickstart] [CITED: https://openrouter.ai/docs/api_reference/authentication]
- OWASP ASVS project page - ASVS version and security-control framing. [CITED: https://owasp.org/www-project-application-security-verification-standard/]

### Tertiary (LOW confidence)
- Assumptions in code examples about exact helper names and launch-smoke implementation details. [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - dependency choices are locked and versions are current from PyPI, but package-legitimacy returned `SUS` for all checked PyPI packages. [VERIFIED: package-legitimacy seam, 2026-08-18]
- Architecture: HIGH - module boundaries and phase scope are defined by local project docs. [VERIFIED: docs/PRD.md:220-261] [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:81-90]
- Pitfalls: MEDIUM - major pitfalls are documented in phase context and project constraints; exact launch-smoke mechanics remain implementation-dependent. [VERIFIED: .planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md:35-36] [ASSUMED]
- Security: MEDIUM - Phase 1 security scope is narrow and locally verified; ASVS category mapping is current but broad. [CITED: https://owasp.org/www-project-application-security-verification-standard/]

**Research date:** 2026-08-18
**Valid until:** 2026-08-25 for package versions and SDK APIs; 2026-09-17 for phase-local architecture decisions.
