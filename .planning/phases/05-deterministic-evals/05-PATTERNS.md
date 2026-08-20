# Phase 5: Deterministic Evals - Pattern Map

**Mapped:** 2026-08-20
**Files analyzed:** 5 (3 new, 2 modified)
**Analogs found:** 5 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/openrouter_demo/evals.py` | service (orchestrator + CLI) | streaming + transform | `src/openrouter_demo/scenarios.py` (async stream orchestration), `src/openrouter_demo/ui.py` `_run_inference` (trace + telemetry assembly) | exact |
| `evals/cases.json` | config (checked-in data) | file I/O (read-only) | `data/api-complaint.csv` + `data/api-complaint-rubric.md` (seed data) | role-match |
| `tests/test_evals.py` | test | request-response (fake stream) | `tests/test_scenarios.py` + `tests/test_ui.py` (fake injected async stream) | exact |
| `tests/test_imports.py` (MODIFY) | test | — | `tests/test_imports.py` (self) | exact |
| `tests/test_phase1_guards.py` (MODIFY) | test | — | `tests/test_phase1_guards.py` (self) | exact |

---

## Pattern Assignments

### `src/openrouter_demo/evals.py` (service / orchestrator, streaming + transform)

Replaces the current stub (whole file today):

```python
class PhaseNotImplementedError(NotImplementedError):
    pass


def main() -> None:
    raise PhaseNotImplementedError("Deterministic eval execution belongs to Phase 5.")
```

**Analog A — `src/openrouter_demo/scenarios.py`** (async stream orchestration + injectable `stream_fn`).

**Imports / stream-fn alias pattern** (`scenarios.py:1-14`):
```python
from __future__ import annotations

import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass

from openrouter_demo.client import OpenRouterError, stream_chat_completion
from openrouter_demo.models import (
    UNAVAILABLE,
    AttemptRecord,
    ...
    StreamChunk,
    StreamedResult,
)
from openrouter_demo.routing import FALLBACK_PRIMARY_STRATEGY, RoutingStrategy

type StreamFn = Callable[..., AsyncIterator[StreamChunk | StreamedResult]]
```

**Core async stream-consume pattern** (`scenarios.py:75-88`, `run_repeat_scenario` run 1 — the shape `run_eval_case` should copy):
```python
    first_result: StreamedResult | None = None
    async for event in stream_fn(prompt, strategy=strategy, api_key=api_key):
        if isinstance(event, StreamedResult):
            first_result = event
```
`run_eval_case` consumes the stream exactly this way, with the default `stream_fn: StreamFn = stream_chat_completion` keyword-injected so tests can swap it.

**Analog B — `src/openrouter_demo/ui.py` `_run_inference`** (trace + `TelemetryEvidence` assembly, lines 328-389).

**Signature + guard** (`ui.py:328-338`):
```python
async def _run_inference(
    prompt: str,
    *,
    api_key: str,
    history: RunHistory,
    stream_fn: StreamFn = stream_chat_completion,
    strategy: RoutingStrategy = DEFAULT_STRATEGY,
    config: AppConfig | None = None,
) -> InferenceRun:
```

**Trace + telemetry assembly** (`ui.py:346-381`) — the exact block `run_eval_case` mirrors, with `name="openrouter-inference"` swapped for `name=f"eval-{case.case_id}"`:
```python
            trace_status: str | Unavailable = UNAVAILABLE
            trace_id: str | None = None
            trace_url: str | None = None
            if config is not None:
                model_for_trace = (
                    event.model if not isinstance(event.model, Unavailable) else strategy.model
                )
                usage_details: dict[str, int] = {}
                if not isinstance(event.prompt_tokens, Unavailable):
                    usage_details["prompt_tokens"] = event.prompt_tokens
                if not isinstance(event.completion_tokens, Unavailable):
                    usage_details["completion_tokens"] = event.completion_tokens
                outcome = record_trace(
                    config=config,
                    name="openrouter-inference",
                    model=model_for_trace,
                    input={"prompt": prompt},
                    output=event.text,
                    usage_details=usage_details,
                )
                trace_status = outcome.status
                trace_id = outcome.trace_id
                trace_url = outcome.trace_url

            telemetry = TelemetryEvidence(
                model=event.model,
                provider=event.provider,
                latency_ms=event.latency_ms,
                prompt_tokens=event.prompt_tokens,
                completion_tokens=event.completion_tokens,
                total_tokens=event.total_tokens,
                cost_usd=event.cost_usd,
                cache_status=event.cache_status,
                cached_tokens=event.cached_tokens,
                cache_write_tokens=event.cache_write_tokens,
                openrouter_metadata=event.openrouter_metadata,
                trace_status=trace_status,
                trace_id=trace_id,
                trace_url=trace_url,
            )
```

**Dependency signatures to reuse verbatim (do NOT re-implement):**

`record_trace` (`telemetry.py:25-34`):
```python
def record_trace(
    config: AppConfig,
    *,
    name: str,
    model: str,
    input: dict,
    output: str,
    usage_details: dict[str, int],
) -> TraceOutcome:
```
Returns `TraceOutcome(status="enabled"|"disabled"|"failed", trace_id: str | None, trace_url: str | None)` (`telemetry.py:18-21`).

`stream_chat_completion` (`client.py:118-124`):
```python
async def stream_chat_completion(
    prompt: str,
    *,
    strategy: RoutingStrategy | None = None,
    model: str | None = None,
    api_key: str,
    http_client: httpx.AsyncClient | None = None,
    request_timeout: float = 60.0,
) -> AsyncIterator[StreamChunk | StreamedResult]:
```
`model` override is a first-class parameter — `--models` routes through `stream_chat_completion(..., model=...)`.

`STRATEGIES` (`routing.py:50-55`) keys are exactly `default` / `cost` / `latency`, values are `RoutingStrategy(name, description, model, provider_preferences)`. `strategy_payload` (`routing.py:57-62`) builds the provider dict.

**Frozen-dataclass convention to replicate** — `models.py:41-57` (`StreamedResult`), `models.py:65-81` (`TelemetryEvidence`):
```python
@dataclass(frozen=True)
class StreamedResult:
    text: str
    model: str | Unavailable
    provider: str | Unavailable
    ...
```
`EvalCase`, `EvalResult`, `EvalSummary` must all be `@dataclass(frozen=True)` and use `tuple[str, ...]` for term lists. `EvalResult.telemetry` is `TelemetryEvidence | None`.

**Sentinels** (`models.py:6-14`): `UNAVAILABLE = Unavailable()`; never coerce to `0`/`0.0`/`""`. Serialization must go through `TelemetryEvidence.to_dict`/`from_dict` (which use `serialize_value`/`deserialize_value`, `models.py:19-33`) — not ad-hoc strings.

**CLI conventions:**
- `main(argv: list[str] | None = None) -> int` (argparse stdlib). Exit contract: `0` = ran; `1` = config error (missing `OPENROUTER_API_KEY`, bad cases file); `2` = unexpected runtime error.
- Guard before network: `config = load_config()`; if `not config.openrouter_ready` → stderr message + `return 1`. (`AppConfig.openrouter_ready` in `config.py:15-19`.)
- Documented invocation: `PYTHONPATH=src uv run python -m openrouter_demo.evals` (because `pyproject.toml:19` `[tool.uv] package = false`).

**Error handling:** no bare network exceptions — consume the stream; on `OpenRouterError` build a failed `EvalResult` (mirroring `ui.py`'s `except OpenRouterError as exc:` branch at `ui.py:390-404`).

---

### `evals/cases.json` (config / checked-in data, file I/O read-only)

**Analog:** `data/api-complaint.csv` (header + rows) and `data/api-complaint-rubric.md` (criteria vocabulary). The JSON is the canonical, checked-in input; the `data/*` files stay read-only seed.

**Header vocabulary to translate into terms** (`data/api-complaint.csv` header line 1):
```
case_id,category,failure_type,frustration_level,seed_ref,customer_message,context,required_behaviors,prohibited_behaviors,binary_criteria,auto_fail,min_tone_score,reference_answer_sketch
```
Each `expected_terms`/`forbidden_terms` list is a keyword translation of that row's `required_behaviors` / `prohibited_behaviors` / `auto_fail` columns (see `data/api-complaint-rubric.md` §1 binary criteria vocabulary: `ACK;NODEF;DIAG;NEXT;NOGUAR;NOBLAME;SCOPE`).

**JSON shape** (top-level `{"cases": [...]}`), 5 cases, each:
```json
{
  "case_id": "complaint-timeout-01",
  "name": "Timeout during launch window",
  "prompt": "...",
  "expected_terms": ["launch", "request id", "timestamp"],
  "forbidden_terms": ["never happen again", "won't happen again", "this is rare"],
  "scoring_notes": "..."
}
```

**Loader validation** (must be 3–5 cases, raising `ValueError` otherwise) — this is the `load_cases` pattern in RESEARCH.md; no codebase analog exists (no existing checked-in JSON loader), so use `json.load` + `tuple(...)`.

---

### `tests/test_evals.py` (test, request-response with fake injected async stream)

**Analog A — `tests/test_scenarios.py`** (fake injected stream + `asyncio.run` collection).

**Fake stream + runner helpers** (`test_scenarios.py:11-58`):
```python
import asyncio
from collections.abc import AsyncIterator

from openrouter_demo.client import OpenRouterHTTPError
from openrouter_demo.models import UNAVAILABLE, Status, StreamChunk, StreamedResult
from openrouter_demo.routing import DEFAULT_STRATEGY, FALLBACK_PRIMARY_STRATEGY
from openrouter_demo.scenarios import FallbackResult, run_fallback_scenario


def _dual_stream() -> object:
    call_count = 0

    async def stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OpenRouterHTTPError(
                "OpenRouter request failed (404)", status_code=404, partial_text=""
            )
        yield StreamChunk("Fallback ")
        yield StreamChunk("response")
        yield StreamedResult(
            text="Fallback response",
            model="openai/gpt-4o-mini",
            provider="OpenAI",
            prompt_tokens=3,
            completion_tokens=4,
            total_tokens=7,
            cost_usd=0.001,
            latency_ms=200,
        )

    return stream
```

**Async runner pattern** (`test_scenarios.py:46-54`):
```python
def _collect_events(stream: object) -> list[object]:
    async def _run() -> list[object]:
        events: list[object] = []
        async for event in run_fallback_scenario(
            "test prompt",
            fallback_strategy=DEFAULT_STRATEGY,
            api_key="sk-test",
            stream_fn=stream,
        ):
            events.append(event)
        return events

    return asyncio.run(_run())
```

**Analog B — `tests/test_ui.py`** (single fake stream + assertions on telemetry fields), lines 23-62:
```python
def test_run_inference_records_successful_stream() -> None:
    async def fake_stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        yield StreamChunk("Hello ")
        yield StreamChunk("there")
        yield StreamedResult(
            text="Hello there",
            model="openai/gpt-4o-mini",
            provider="OpenAI",
            prompt_tokens=3,
            completion_tokens=4,
            total_tokens=7,
            cost_usd=0.001,
            latency_ms=321,
        )

    history = RunHistory()
    run = _run(
        _run_inference(
            "Explain streaming", api_key="sk-test", history=history, stream_fn=fake_stream
        )
    )

    assert run.status is Status.SUCCEEDED
    assert run.streamed_text == "Hello there"
    assert run.strategy_name == DEFAULT_STRATEGY.name
    assert run.telemetry is not None
    assert run.telemetry.model == "openai/gpt-4o-mini"
    assert run.telemetry.provider == "OpenAI"
    assert run.telemetry.latency_ms == 321
```

**Unavailable-preservation test pattern** (`test_ui.py:65-84`) — the model for `test_run_eval_case_preserves_unavailable`:
```python
def test_run_inference_preserves_unavailable_metadata() -> None:
    async def fake_stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        yield StreamedResult(
            text="done",
            model=UNAVAILABLE,
            provider=UNAVAILABLE,
            prompt_tokens=UNAVAILABLE,
            completion_tokens=UNAVAILABLE,
            total_tokens=UNAVAILABLE,
            cost_usd=UNAVAILABLE,
            latency_ms=12,
        )
    ...
    assert run.telemetry.model is UNAVAILABLE
```

**Trace-status + monkeypatch pattern** (`test_telemetry.py:154-190`) — the model for `test_run_eval_case_trace_disabled_and_enabled` and `test_run_eval_case_trace_input_has_no_api_key`:
```python
def test_run_inference_trace_input_contains_no_api_key(monkeypatch) -> None:
    captured: dict = {}

    async def fake_stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        yield StreamChunk("hi")
        yield StreamedResult(...)

    def fake_record_trace(config, *, name, model, input, output, usage_details):
        captured["input"] = input
        return TraceOutcome(status="disabled", trace_id=None, trace_url=None)

    monkeypatch.setattr("openrouter_demo.ui.record_trace", fake_record_trace)
    ...
    assert captured["input"] == {"prompt": "Prompt"}
    assert "api_key" not in captured["input"]
```
For evals, the monkeypatch target is `"openrouter_demo.evals.record_trace"`.

**Disabled-trace test** (`test_telemetry.py:147-155`):
```python
def test_record_trace_disabled_without_credentials() -> None:
    outcome = record_trace(
        load_config({}),
        name="n",
        model="m",
        input={},
        output="o",
        usage_details={},
    )
    assert outcome == TraceOutcome(status="disabled", trace_id=None, trace_url=None)
```

**Test naming convention:** `test_<subject>_<behavior>` snake_case, plain `assert`, no test classes, no fixtures — module-level helper functions returning fake streams.

---

### `tests/test_imports.py` (MODIFY — two tests change)

Current assertions that will break when `evals.py` is implemented and `evals/cases.json` lands:

**Test 1** (`test_imports.py:51-55`) — expects the stub to raise; must become "no longer raises `PhaseNotImplementedError`, returns an int":
```python
def test_live_boundaries_raise_honest_phase_errors() -> None:
    assert callable(run_fallback_scenario)
    assert issubclass(ScenarioNotImplemented, NotImplementedError)
    with pytest.raises(EvalsNotImplemented, match="Phase 5"):
        evals_main()
```

**Test 2** (`test_imports.py:98-100`) — asserts `cases.json` does NOT exist; must be rewritten to assert it now exists with 3–5 cases:
```python
def test_evals_directory_has_no_phase1_cases() -> None:
    assert Path("evals/.gitkeep").exists()
    assert not Path("evals/cases.json").exists()
```

**Related import at top** (`test_imports.py:12-13`) — keep or remove `PhaseNotImplementedError` in lockstep with `evals.py`:
```python
from openrouter_demo.evals import PhaseNotImplementedError as EvalsNotImplemented
from openrouter_demo.evals import main as evals_main
```

---

### `tests/test_phase1_guards.py` (MODIFY — guard patterns, may not need changes)

**Guard patterns to preserve** (`test_phase1_guards.py:1-33`):
```python
from pathlib import Path

SOURCE_PATHS = [Path("app.py"), *Path("src/openrouter_demo").glob("*.py")]


def implementation_text() -> str:
    # sqlite_store.py is the Phase 4 persistence layer and intentionally imports
    # sqlite3; the "no database" guard covers the core inference modules only.
    paths = [p for p in SOURCE_PATHS if p.name != "sqlite_store.py"]
    return "\n".join(path.read_text() for path in paths)
```

The Langfuse isolation guard keeps a hardcoded `core_modules` list that **does not include `evals.py`** (`test_phase1_guards.py:25-33`):
```python
def test_phase1_keeps_langfuse_tracing_isolated_to_telemetry() -> None:
    telemetry_path = Path("src/openrouter_demo/telemetry.py")
    assert "get_client(" in telemetry_path.read_text()
    core_modules = [
        Path("app.py"),
        Path("src/openrouter_demo/client.py"),
        Path("src/openrouter_demo/models.py"),
        Path("src/openrouter_demo/scenarios.py"),
        Path("src/openrouter_demo/ui.py"),
    ]
    for path in core_modules:
        assert "get_client(" not in path.read_text()
```

**Implication for Phase 5:** `evals.py` is auto-covered by `test_phase1_has_no_fastapi_product_layer` and `test_phase1_has_no_database_imports` (via the `*.py` glob in `SOURCE_PATHS`), but NOT by the Langfuse isolation list. To enforce "evals must go through `telemetry.record_trace`, never `langfuse.get_client()` directly", add `Path("src/openrouter_demo/evals.py")` to the `core_modules` list in this test. `evals.py` itself must never import `sqlite3`/`fastapi`/`sqlalchemy`/`psycopg`/`asyncpg`, and must call `record_trace` (which already passes the isolation guard).

---

## Shared Patterns

### Metadata honesty / `Unavailable` sentinel
**Source:** `src/openrouter_demo/models.py:6-33`
**Apply to:** `evals.py` (`EvalResult`, `TelemetryEvidence` assembly), `tests/test_evals.py`
```python
@dataclass(frozen=True)
class Unavailable:
    label: str = "unavailable"

    def __bool__(self) -> bool:
        return False


UNAVAILABLE = Unavailable()

_UNAVAILABLE_SENTINEL = "__unavailable__"


def serialize_value(value: object) -> object:
    if isinstance(value, Unavailable):
        return _UNAVAILABLE_SENTINEL
    return value
```
Rule: never coerce missing tokens/cost/trace to `0`/`0.0`/`""`; use `UNAVAILABLE`. Serialize via `TelemetryEvidence.to_dict()`/`from_dict()`.

### Trace creation (Langfuse isolation)
**Source:** `src/openrouter_demo/telemetry.py:25-50`
**Apply to:** `evals.py` only through `record_trace` (never `langfuse.get_client()` directly); `tests/test_phase1_guards.py` (add `evals.py` to `core_modules`).
```python
def record_trace(config, *, name, model, input, output, usage_details) -> TraceOutcome:
    if not config.langfuse_ready:
        return TraceOutcome(status="disabled", trace_id=None, trace_url=None)
    try:
        from langfuse import get_client
        ...
    except Exception:  # noqa: BLE001
        return TraceOutcome(status="failed", trace_id=None, trace_url=None)
```
Eval trace name must be `f"eval-{case.case_id}"` (distinct from UI's `"openrouter-inference"`).

### Inject a `stream_fn` for zero-network tests
**Source:** `src/openrouter_demo/scenarios.py:14`, `src/openrouter_demo/ui.py:333`
**Apply to:** `evals.py` `run_eval_case`/`run_eval_set`, `tests/test_evals.py`
```python
type StreamFn = Callable[..., AsyncIterator[StreamChunk | StreamedResult]]
```
Every test injects a fake `async def fake_stream(*_args, **_kwargs)` yielding `StreamChunk` + `StreamedResult`, never touching the network.

### Config guard before network
**Source:** `src/openrouter_demo/config.py:5-27`
**Apply to:** `evals.main()`
```python
@dataclass(frozen=True)
class AppConfig:
    openrouter_ready: bool
    langfuse_ready: bool
    missing_required: tuple[str, ...]
    missing_langfuse: tuple[str, ...]
```
`main()` checks `load_config().openrouter_ready` first; missing `OPENROUTER_API_KEY` → stderr + `return 1`, no network.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `evals/cases.json` loader (`load_cases`) | utility | file I/O (JSON) | No existing checked-in JSON loader in `src/`; `sqlite_store.py` is the only data layer but is DB-backed. Use RESEARCH.md's `json.load` + 3–5 case `ValueError` pattern. |
| `EvalSummary` aggregation | model | transform | No existing grouping/aggregation over results; closest is `ui.py` comparison-table rendering but it's UI-bound. Follow RESEARCH.md's `by_strategy()` grouping. |

## Metadata

**Analog search scope:** `src/openrouter_demo/` (all modules), `tests/`, `data/`, `evals/`, `pyproject.toml`
**Files scanned:** 16 (client, config, evals, history, models, routing, scenarios, telemetry, ui, app.py, 5 test files, 3 data files, pyproject.toml)
**Pattern extraction date:** 2026-08-20
