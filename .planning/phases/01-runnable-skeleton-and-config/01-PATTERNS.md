# Phase 1: Runnable Skeleton and Config - Pattern Map

**Mapped:** 2026-08-18
**Files analyzed:** 17
**Analogs found:** 0 / 17 code analogs; 17 / 17 seed-document analogs

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `app.py` | route / entrypoint | request-response startup | `.planning/phases/01-runnable-skeleton-and-config/01-RESEARCH.md` | seed-doc |
| `pyproject.toml` | config | batch / setup | `.planning/phases/01-runnable-skeleton-and-config/01-RESEARCH.md` | seed-doc |
| `uv.lock` | config | batch / setup | `docs/specs/quickstart.md` | seed-doc |
| `.env.example` | config | file-I/O / setup | `docs/specs/quickstart.md` + `.gitignore` | seed-doc |
| `README.md` | documentation | static setup flow | `docs/specs/quickstart.md` | seed-doc |
| `src/openrouter_demo/__init__.py` | config / package | import boundary | `docs/PRD.md` | seed-doc |
| `src/openrouter_demo/config.py` | config / utility | transform | `.planning/phases/01-runnable-skeleton-and-config/01-RESEARCH.md` | seed-doc |
| `src/openrouter_demo/ui.py` | component | event-driven | `docs/ux/screen-spec.md` + research NiceGUI example | seed-doc |
| `src/openrouter_demo/client.py` | service | streaming / request-response | `docs/PRD.md` + `docs/specs/research.md` | seed-doc |
| `src/openrouter_demo/routing.py` | config / utility | transform | `docs/specs/data-model.md` + `docs/ux/screen-spec.md` | seed-doc |
| `src/openrouter_demo/scenarios.py` | service | event-driven orchestration | `.planning/research/ARCHITECTURE.md` | seed-doc |
| `src/openrouter_demo/telemetry.py` | service / utility | transform / event-driven | `docs/specs/data-model.md` + `docs/ux/screen-spec.md` | seed-doc |
| `src/openrouter_demo/evals.py` | service / utility | batch / file-I/O | `docs/specs/contracts/local-demo-contract.md` + `data/api-complaint-rubric.md` | seed-doc |
| `src/openrouter_demo/models.py` | model | transform | `docs/specs/data-model.md` | seed-doc |
| `evals/.gitkeep` | data / config | file-I/O | `docs/specs/data-model.md` + `data/api-complaint.csv` | seed-doc |
| `tests/test_config.py` | test | request-response / transform | `.planning/phases/01-runnable-skeleton-and-config/01-RESEARCH.md` | seed-doc |
| `tests/test_imports.py` | test | batch / importability | `.planning/phases/01-runnable-skeleton-and-config/01-CONTEXT.md` | seed-doc |

## Pattern Assignments

### `app.py` (route / entrypoint, request-response startup)

**Analog:** No existing code analog. Use the research startup example and PRD boundary.

**Core entrypoint pattern** (`.planning/phases/01-runnable-skeleton-and-config/01-RESEARCH.md` lines 263-273):
```python
# Source: NiceGUI docs via Context7 and PRD app.py boundary.
from nicegui import ui

from openrouter_demo.config import load_config
from openrouter_demo.ui import build_app


build_app(load_config())

ui.run(title="OpenRouter Production Inference Lab")
```

**Boundary pattern** (`docs/PRD.md` lines 253-261):
```text
### `app.py`

Thin entry point that loads configuration, registers the NiceGUI UI, and starts the local demo server.

### `ui.py`

NiceGUI screen composition for prompt input, scenario selection, streaming display, telemetry display, trace links, and TailwindCSS styling classes.

Business/inference logic should remain outside the UI.
```

---

### `pyproject.toml` (config, batch / setup)

**Analog:** No existing code analog. Use the research pyproject skeleton, then generate `uv.lock` from it.

**Project metadata and tooling pattern** (`.planning/phases/01-runnable-skeleton-and-config/01-RESEARCH.md` lines 350-374):
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

**Dependency checkpoint pattern** (`.planning/phases/01-runnable-skeleton-and-config/01-RESEARCH.md` lines 149-163): planner should add a human verification checkpoint before installing the flagged packages, because the research package-legitimacy seam marked `nicegui`, `httpx`, `langfuse`, `pytest`, `ruff`, and `uv` as `SUS`.

---

### `uv.lock` (config, batch / setup)

**Analog:** No existing code analog. Generate via `uv sync` / `uv lock`; do not hand-edit.

**Command pattern** (`docs/specs/quickstart.md` lines 13-19):
```sh
uv sync
```

**Reviewer command pattern** (`.planning/phases/01-runnable-skeleton-and-config/01-RESEARCH.md` lines 139-145):
```bash
uv sync
uv run python app.py
uv run pytest
uv run ruff check .
```

---

### `.env.example` (config, file-I/O / setup)

**Analog:** No existing `.env.example`. Use quickstart env names and existing `.gitignore` secret handling.

**Credential names pattern** (`docs/specs/quickstart.md` lines 21-37):
```sh
export OPENROUTER_API_KEY="..."
# Optional tracing:
export LANGFUSE_PUBLIC_KEY="..."
export LANGFUSE_SECRET_KEY="..."
export LANGFUSE_BASE_URL="..."
```

**Secret-ignore pattern** (`.gitignore` lines 126-128):
```gitignore
# Environments
.env
.venv
```

**Phase constraint:** `.env.example` must contain variable names and comments only, never secret-like values (`01-CONTEXT.md` lines 21-25).

---

### `README.md` (documentation, static setup flow)

**Analog:** No existing README. Use quickstart for setup structure and keep Phase 6 storytelling deferred.

**Setup flow pattern** (`docs/specs/quickstart.md` lines 13-45):
```sh
uv sync
uv run python app.py
```

Expected README sections for Phase 1:
- Project purpose in one short paragraph.
- Prerequisites: Python 3.12+, `uv`, required OpenRouter key, optional Langfuse keys.
- Setup: `uv sync`.
- Environment variables: required `OPENROUTER_API_KEY`, optional `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`.
- Launch: `uv run python app.py`.
- Future capabilities clearly marked as later phases.

---

### `src/openrouter_demo/__init__.py` (config / package, import boundary)

**Analog:** No existing package. Use PRD layout and keep the module importable with minimal package metadata only.

**Package layout pattern** (`docs/PRD.md` lines 228-238):
```text
|-- src/
|   |-- openrouter_demo/
|       |-- __init__.py
|       |-- client.py      # OpenRouter streaming + errors + metadata
|       |-- config.py      # env vars and defaults
|       |-- evals.py       # eval cases + scoring
|       |-- models.py      # typed result/telemetry structures
|       |-- routing.py     # model/provider strategies + fallbacks
|       |-- scenarios.py   # deterministic demo scenarios
|       |-- telemetry.py   # Langfuse + normalized runtime metrics
|       |-- ui.py          # NiceGUI views/components
```

---

### `src/openrouter_demo/config.py` (config / utility, transform)

**Analog:** No existing code analog. Use research env-only configuration object.

**Imports and model pattern** (`.planning/phases/01-runnable-skeleton-and-config/01-RESEARCH.md` lines 227-237):
```python
# Source: Phase 1 context and Langfuse docs via Context7.
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    openrouter_ready: bool
    langfuse_ready: bool
    missing_required: tuple[str, ...]
```

**Core config pattern** (`.planning/phases/01-runnable-skeleton-and-config/01-RESEARCH.md` lines 240-255):
```python
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

**Error handling pattern:** Do not raise at startup for missing `OPENROUTER_API_KEY`; missing credentials are setup state (`01-CONTEXT.md` lines 22-24).

---

### `src/openrouter_demo/ui.py` (component, event-driven)

**Analog:** No existing NiceGUI code. Use research NiceGUI example and screen-spec structure.

**Imports pattern** (`.planning/phases/01-runnable-skeleton-and-config/01-RESEARCH.md` lines 397-403):
```python
# Source: NiceGUI docs via Context7 and screen-spec labels.
from nicegui import ui

from openrouter_demo.config import AppConfig
```

**Core shell pattern** (`.planning/phases/01-runnable-skeleton-and-config/01-RESEARCH.md` lines 405-416):
```python
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

**Screen structure pattern** (`docs/ux/screen-spec.md` lines 13-21):
```text
Header
Request + Strategy
Streaming Response + Telemetry
Run History / Comparison
Eval Summary
```

**Required labels** (`docs/ux/screen-spec.md` lines 27-82): use `OpenRouter Production Inference Lab`, `Route, observe, recover, and evaluate model calls.`, `Prompt`, `Sample prompt`, and `Run Inference`.

**Empty/disabled states:** Phase 1 panels should be present but honest. Use the empty-state copy from `docs/ux/screen-spec.md` lines 182-188, 287-291, and 331-335 where useful. Do not display fake model/provider/cost/cache/trace values.

---

### `src/openrouter_demo/client.py` (service, streaming / request-response)

**Analog:** No existing code analog. Phase 1 should create an importable honest stub only.

**Future ownership pattern** (`docs/PRD.md` lines 231-232 and `docs/PRD.md` lines 263-265):
```text
|       |-- client.py      # OpenRouter streaming + errors + metadata
```

```text
OpenRouter integration for request construction, streaming, timeout handling, API exceptions, response normalization, and available usage metadata.
```

**Direct OpenRouter constraint** (`docs/specs/research.md` lines 3-8):
```text
Use direct OpenRouter Chat Completions requests over HTTPS
```

**Stub pattern** (`.planning/phases/01-runnable-skeleton-and-config/01-RESEARCH.md` lines 276-291):
```python
# Source: Phase 1 D-02 requires honest, importable stubs.
class PhaseNotImplementedError(RuntimeError):
    pass


def stream_chat_completion(*_: object, **__: object) -> None:
    raise PhaseNotImplementedError(
        "Live OpenRouter streaming is planned for Phase 2."
    )
```

---

### `src/openrouter_demo/routing.py` (config / utility, transform)

**Analog:** No existing code analog. Use data-model strategy definitions and screen-spec labels.

**Future ownership pattern** (`docs/PRD.md` lines 235-236):
```text
|       |-- routing.py     # model/provider strategies + fallbacks
```

**Strategy model pattern** (`docs/specs/data-model.md` lines 38-58):
```text
Represents a named route selection mode for OpenRouter requests.

- `name`: `default`, `cost`, `latency`, or `custom`.
- `description`: Reviewer-facing explanation of the strategy.
- `models`: Ordered OpenRouter model identifiers considered by the request.
- `provider_preferences`: Provider routing options such as order, allow/deny filters, price
  sorting, latency preference, and fallback allowance.
```

**Phase 1 behavior:** export labels or lightweight dataclasses/constants if useful, but do not imply live provider behavior. Strategy labels should match `docs/ux/screen-spec.md` lines 106-170.

---

### `src/openrouter_demo/scenarios.py` (service, event-driven orchestration)

**Analog:** No existing code analog. Create an importable stub and keep real scenario execution for later phases.

**Architecture ownership pattern** (`.planning/research/ARCHITECTURE.md` lines 23-35):
```text
| `scenarios.py` | Default, cost, latency, fallback, repeat/cache, eval scenario orchestration | routing, client, telemetry |
```

**Future data flow pattern** (`.planning/research/ARCHITECTURE.md` lines 39-45):
```text
1. User selects a scenario and routing strategy in the NiceGUI UI.
2. UI validates prompt and credentials, then starts an async run.
3. Scenario builds a request using `routing.py` and sends it through `client.py`.
4. Client streams chunks and surfaces partial text, usage, router metadata, and errors.
5. Telemetry records observed latency, model/provider, cost/tokens when available, fallback status, cache/repeat state, and trace state.
6. UI updates the response panel and run history as evidence arrives.
7. Eval command reuses the same client/telemetry path, then scores deterministic cases.
```

**Phase 1 behavior:** do not wire orchestration yet; use honest stub functions or constants only.

---

### `src/openrouter_demo/telemetry.py` (service / utility, transform / event-driven)

**Analog:** No existing code analog. Create an importable stub around explicit unavailable states.

**Telemetry fields pattern** (`docs/specs/data-model.md` lines 78-101):
```text
Represents normalized observable data for a run.

- `model`: Reported model identifier or unavailable.
- `provider`: Reported provider identifier or unavailable.
- `latency_ms`: Observed local latency.
- `prompt_tokens`: Reported prompt tokens or unavailable.
- `completion_tokens`: Reported completion tokens or unavailable.
- `total_tokens`: Reported total tokens or unavailable.
- `cost_usd`: Reported or calculated cost when source data supports it; otherwise unavailable.
- `cache_status`: Reported cache hit/miss/status or unavailable.
- `repeat_observation`: Observed repeat-run latency/cost comparison when cache metadata is unavailable.
- `fallback_used`: Boolean.
- `trace_status`: `enabled`, `disabled`, or `failed`.
- `trace_url`: Link when Langfuse tracing succeeds.
```

**UI copy pattern** (`docs/ux/screen-spec.md` lines 239-261): use explicit unavailable/disabled language such as `Unavailable from selected route/provider.` and `Langfuse tracing disabled. Configure Langfuse credentials to enable trace links.`

**Phase 1 behavior:** do not create Langfuse traces yet. Missing Langfuse credentials are optional disabled state, not an error.

---

### `src/openrouter_demo/evals.py` (service / utility, batch / file-I/O)

**Analog:** No existing code analog. Create an importable stub; do not run evals in Phase 1.

**Command contract pattern** (`docs/specs/contracts/local-demo-contract.md` lines 79-111):
```sh
uv run python -m openrouter_demo.evals
```

The future command reads `evals/cases.json`, reports pass/fail and score reason for each case, and exits failure when setup is invalid or the runner cannot complete configured cases.

**Eval model pattern** (`docs/specs/data-model.md` lines 103-137): future eval cases need `case_id`, `name`, `prompt`, deterministic criteria, and result `passed` plus `score_reason`.

**Seed rubric pattern** (`data/api-complaint-rubric.md` lines 7-12):
```text
1. **Binary criteria** — hard requirements. Each is 1 or 0. Only the criteria listed in that row's `binary_criteria` column apply.
2. **Tone score** — a single 1–5 quality judgment, compared against the row's `min_tone_score`.

Plus **auto-fail conditions**, which zero the case regardless of the other scores.
```

**Phase 1 behavior:** keep eval execution deferred; if a callable exists, it should raise a Phase 1 not-implemented error rather than producing fake scores.

---

### `src/openrouter_demo/models.py` (model, transform)

**Analog:** No existing code analog. Use `docs/specs/data-model.md`; define only enough lightweight types for Phase 1 config/UI if needed.

**Inference run model pattern** (`docs/specs/data-model.md` lines 3-28): future runs include `run_id`, `scenario`, `prompt`, `strategy_name`, timestamps, status, streamed text, error message, telemetry, and fallback attempt. Missing metadata must be represented as unavailable, not guessed.

**Routing strategy model pattern** (`docs/specs/data-model.md` lines 38-58): future strategy names are `default`, `cost`, `latency`, or `custom`.

**Telemetry model pattern** (`docs/specs/data-model.md` lines 78-101): unavailable provider metadata, tokens, cost, cache, and trace URL must remain distinguishable from zero values.

---

### `evals/.gitkeep` (data / config, file-I/O)

**Analog:** No existing `evals/` directory. The repo has seed CSV/rubric material, but Phase 1 should not wire eval execution or create fake cases.

**Future eval case pattern** (`docs/specs/data-model.md` lines 103-120):
```text
- `case_id`: Stable identifier.
- `name`: Human-readable label.
- `prompt`: Eval prompt.
- `expected_terms`: Terms or criteria required for pass.
- `forbidden_terms`: Optional terms that fail the case.
- `scoring_notes`: Reviewer-facing scoring explanation.
```

**Resolved Phase 1 placeholder:** Use `evals/.gitkeep` or `evals/README.md` instead of `evals/cases.json`; do not create fake eval cases until the eval phase owns executable cases.

---

### `tests/test_config.py` (test, request-response / transform)

**Analog:** No existing tests. Use research pytest pattern.

**Imports and config assertions** (`.planning/phases/01-runnable-skeleton-and-config/01-RESEARCH.md` lines 377-395):
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

**Additional expected assertions:** complete Langfuse env vars set `langfuse_ready=True`; incomplete Langfuse env vars keep `langfuse_ready=False`; config never exposes secret values.

---

### `tests/test_imports.py` (test, batch / importability)

**Analog:** No existing tests. Use Phase 1 importability requirement.

**Importability source** (`01-CONTEXT.md` lines 16-18 and 87-90):
```text
Create the full importable scaffold in Phase 1: `app.py`, `pyproject.toml`, `uv.lock`, `.env.example`, package modules for UI/client/routing/scenarios/telemetry/evals/models/config, `tests/`, and `evals/`.
```

**Test pattern:** import every scaffold module directly:
```python
def test_scaffold_modules_import() -> None:
    import openrouter_demo.client
    import openrouter_demo.config
    import openrouter_demo.evals
    import openrouter_demo.models
    import openrouter_demo.routing
    import openrouter_demo.scenarios
    import openrouter_demo.telemetry
    import openrouter_demo.ui
```

## Shared Patterns

### No Code Analogs Yet

**Source:** `01-CONTEXT.md` lines 77-83

Apply to all new source files:
```text
Seed docs in `docs/` and planning docs in `.planning/` are the primary reusable assets. There is no implemented app/source scaffold yet.

The repo currently establishes product and architecture decisions through docs, not code.
```

### Env-Only Configuration

**Source:** `01-CONTEXT.md` lines 20-25 and `docs/specs/research.md` lines 64-72

Apply to: `config.py`, `ui.py`, `.env.example`, `tests/test_config.py`, README setup docs.

Pattern:
- Read runtime config through `os.environ` only.
- Required: `OPENROUTER_API_KEY`.
- Optional: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`.
- Missing OpenRouter key must produce setup state, not a process crash.
- Missing Langfuse variables must show disabled optional tracing.
- Do not add dotenv parsing in Phase 1.

### Honest Stubs

**Source:** `01-CONTEXT.md` lines 17-18 and `01-RESEARCH.md` lines 276-291

Apply to: `client.py`, `routing.py`, `scenarios.py`, `telemetry.py`, `evals.py`, and any model placeholders.

Pattern:
- Modules import cleanly.
- Later-phase behavior either absent or raises a clear `PhaseNotImplementedError`.
- Do not display fake telemetry, provider, model, cache, trace, routing, fallback, or eval results.

### UI Separation

**Source:** `docs/PRD.md` lines 253-261 and `docs/specs/acceptance-criteria.md` lines 73-84

Apply to: `app.py`, `ui.py`, `client.py`, `routing.py`, `telemetry.py`, `scenarios.py`, `evals.py`.

Pattern:
- `app.py` is launch glue.
- `ui.py` builds NiceGUI layout and setup/status shells.
- Business and inference logic stay outside UI.
- Do not present FastAPI as a separate product architecture layer.

### Metadata Honesty

**Source:** `docs/specs/data-model.md` lines 22-28 and 97-101; `docs/ux/screen-spec.md` lines 239-261

Apply to: `models.py`, `telemetry.py`, `ui.py`, future `client.py`, tests.

Pattern:
- Missing provider, token, cost, trace, and cache data is unavailable, not zero.
- `trace_url` exists only when tracing succeeds.
- Cost values need source data or explicit unavailable state.

### Quality Gates

**Source:** `docs/specs/contracts/local-demo-contract.md` lines 113-125 and `docs/specs/quickstart.md` lines 107-118

Apply to: `pyproject.toml`, `uv.lock`, tests, README.

Pattern:
```sh
uv run pytest
uv run ruff check .
```

Phase 1 also needs `uv sync` and launch smoke check for `uv run python app.py` without live OpenRouter request.

## No Analog Found

No implemented code analogs exist in the repository. The current repo contains seed docs, planning docs, and data files only; `find` found no `.py`, `pyproject.toml`, `uv.lock`, or `.env.example` files outside the requested planning artifact.

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `app.py` | route / entrypoint | request-response startup | No app entrypoint exists. Use research and PRD patterns. |
| `pyproject.toml` | config | batch / setup | No Python project metadata exists. Use research pyproject skeleton. |
| `uv.lock` | config | batch / setup | No lockfile exists. Generate from `uv`. |
| `.env.example` | config | file-I/O / setup | No example env file exists. Use quickstart env names; `.gitignore` already ignores `.env`. |
| `README.md` | documentation | static setup flow | No README exists. Use quickstart setup flow. |
| `src/openrouter_demo/__init__.py` | config / package | import boundary | No package exists. Use PRD layout. |
| `src/openrouter_demo/config.py` | config / utility | transform | No config module exists. Use research env-only config example. |
| `src/openrouter_demo/ui.py` | component | event-driven | No UI module exists. Use screen spec and research NiceGUI example. |
| `src/openrouter_demo/client.py` | service | streaming / request-response | No client module exists. Create honest importable stub only. |
| `src/openrouter_demo/routing.py` | config / utility | transform | No routing module exists. Use docs for future strategy ownership. |
| `src/openrouter_demo/scenarios.py` | service | event-driven orchestration | No scenario module exists. Use architecture doc for ownership only. |
| `src/openrouter_demo/telemetry.py` | service / utility | transform / event-driven | No telemetry module exists. Use data model for future fields. |
| `src/openrouter_demo/evals.py` | service / utility | batch / file-I/O | No eval runner exists. Create honest importable stub only. |
| `src/openrouter_demo/models.py` | model | transform | No model module exists. Use data model docs. |
| `evals/.gitkeep` | data / config | file-I/O | No eval directory exists. Use an honest directory marker and avoid fake cases. |
| `tests/test_config.py` | test | request-response / transform | No tests exist. Use research pytest example. |
| `tests/test_imports.py` | test | batch / importability | No tests exist. Use importable scaffold requirement. |

## Metadata

**Analog search scope:** repository root excluding `.git`; searched implemented Python/project files and seed docs.
**Files scanned:** 30 repository files via `rg --files --hidden` plus targeted seed-doc ranges.
**Pattern extraction date:** 2026-08-18
**Project instruction sources:** `AGENTS.md`; `.codex/skills/gsd-plan-phase/SKILL.md`; `.agents/skills/impeccable/SKILL.md` checked because Phase 1 context mentions later UI polish.
