# Phase 3: Routing and Fallback Demo - Pattern Map

**Mapped:** 2026-08-19
**Files analyzed:** 10 (6 modified, 2 new, 2 extended tests)
**Analogs found:** 8 / 10

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/openrouter_demo/routing.py` | config/model | request-response | `src/openrouter_demo/config.py` | exact (frozen dataclass pattern) |
| `src/openrouter_demo/models.py` | model | transform | `src/openrouter_demo/models.py` (itself) | exact (extend existing types) |
| `src/openrouter_demo/scenarios.py` | service | streaming | `src/openrouter_demo/client.py` | role-match (async generator yielding StreamChunk/StreamedResult) |
| `src/openrouter_demo/client.py` | service | streaming | `src/openrouter_demo/client.py` (itself) | exact (no changes needed — verify only) |
| `src/openrouter_demo/ui.py` | component | event-driven | `src/openrouter_demo/ui.py` (itself) | exact (extend existing handlers + rendering) |
| `src/openrouter_demo/history.py` | store | CRUD | `src/openrouter_demo/history.py` (itself) | exact (no changes needed — verify only) |
| `tests/test_routing.py` | test | request-response | `tests/test_client.py` | exact (same assertion + injected mock pattern) |
| `tests/test_scenarios.py` | test | streaming | `tests/test_ui.py` | exact (injected async streams, no network) |
| `tests/test_ui.py` | test | event-driven | `tests/test_ui.py` (itself) | exact (extend existing test functions) |
| `tests/test_imports.py` | test | request-response | `tests/test_imports.py` (itself) | exact (update import + stub expectations) |

## Pattern Assignments

### `src/openrouter_demo/routing.py` (config/model, request-response)

**Analog:** `src/openrouter_demo/config.py` (frozen dataclass pattern) and itself (extending existing `RoutingStrategy`)

**Imports pattern** (lines 1-3):
```python
from dataclasses import dataclass
from typing import Literal

StrategyName = Literal["default", "cost", "latency", "custom"]
```

**Core pattern — frozen dataclass strategy + label dict** (lines 6-27):
```python
ROUTING_STRATEGY_LABELS: dict[StrategyName, str] = {
    "default": "Default",
    "cost": "Cost optimized",
    "latency": "Latency optimized",
    "custom": "Custom",
}


@dataclass(frozen=True)
class RoutingStrategy:
    name: StrategyName
    description: str
    model: str
    provider_preferences: dict[str, object] | None


DEFAULT_STRATEGY = RoutingStrategy(
    name="default",
    description="Balanced route for general quality and availability.",
    model="openai/gpt-4o-mini",
    provider_preferences=None,
)
```

**What to add:** `COST_STRATEGY`, `LATENCY_STRATEGY`, `FALLBACK_PRIMARY_STRATEGY` instances following the exact same `RoutingStrategy(...)` constructor pattern. Do NOT change `ROUTING_STRATEGY_LABELS` (guarded by `test_imports.py:46-51`).

**Payload function — currently incomplete** (lines 33-34):
```python
def strategy_payload(strategy: RoutingStrategy) -> dict[str, object]:
    return {"model": strategy.model}
```

**What to change:** Add `provider` key when `provider_preferences is not None`:
```python
def strategy_payload(strategy: RoutingStrategy) -> dict[str, object]:
    payload: dict[str, object] = {"model": strategy.model}
    if strategy.provider_preferences is not None:
        payload["provider"] = strategy.provider_preferences
    return payload
```

**Verification:** `client.py:80-84` already merges `strategy_payload()` into the request body via `{**strategy_payload(strategy), "messages": [...], "stream": True}`. The `provider` key will flow through automatically — no client changes needed.

---

### `src/openrouter_demo/models.py` (model, transform)

**Analog:** itself — extend existing types

**Core pattern — frozen dataclass with UNAVAILABLE sentinel** (lines 1-12):
```python
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


@dataclass(frozen=True)
class Unavailable:
    label: str = "unavailable"

    def __bool__(self) -> bool:
        return False


UNAVAILABLE = Unavailable()
```

**Status enum pattern** (lines 15-21):
```python
class Status(StrEnum):
    PENDING = "pending"
    STREAMING = "streaming"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

**What to add:** `FALLBACK_SUCCEEDED = "fallback_succeeded"` to `Status` enum (after `SUCCEEDED`, before `FAILED` or at end — alphabetical not required, StrEnum preserves insertion order).

**Telemetry/result dataclass pattern** (lines 24-34, 37-45):
```python
@dataclass(frozen=True)
class StreamedResult:
    text: str
    model: str | Unavailable
    provider: str | Unavailable
    prompt_tokens: int | Unavailable
    completion_tokens: int | Unavailable
    total_tokens: int | Unavailable
    cost_usd: float | Unavailable
    latency_ms: int
```

**What to add — AttemptRecord** (follow exact same field pattern with UNAVAILABLE sentinels):
```python
@dataclass(frozen=True)
class AttemptRecord:
    model: str
    provider: str | Unavailable
    status: Status
    error_message: str | None
    latency_ms: int
```

**What to add — FallbackEvidence:**
```python
@dataclass(frozen=True)
class FallbackEvidence:
    primary: AttemptRecord
    fallback: AttemptRecord
```

**InferenceRun pattern** (lines 48-58):
```python
@dataclass(frozen=True)
class InferenceRun:
    run_id: str
    prompt: str
    strategy_name: str
    started_at: datetime
    completed_at: datetime | None
    status: Status
    streamed_text: str
    error_message: str | None
    telemetry: TelemetryEvidence | None
```

**What to add to InferenceRun:** `fallback_evidence: FallbackEvidence | None = None` as a new field with a default. This preserves backward compatibility — existing `InferenceRun(...)` constructions in `ui.py:175-186` and tests that don't pass `fallback_evidence` will still work.

**IMPORTANT:** Because `InferenceRun` is `frozen=True` and used with positional args in tests (`test_ui.py:115-130`), adding a field with a default at the END of the dataclass is safe. Do NOT reorder existing fields.

---

### `src/openrouter_demo/scenarios.py` (service, streaming)

**Analog:** `src/openrouter_demo/client.py` (async generator yielding StreamChunk/StreamedResult) + `src/openrouter_demo/ui.py:_run_inference` (stream consumption + InferenceRun assembly)

**Current stub** (lines 1-5):
```python
class PhaseNotImplementedError(NotImplementedError):
    pass


def run_scenario(*args: object, **kwargs: object) -> None:
    raise PhaseNotImplementedError("Routing, fallback, and repeat scenarios belong to later phases.")
```

**Pattern to follow — async generator yielding typed events** (from `client.py:65-67`):
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

**Pattern to follow — stream consumption + error capture** (from `ui.py:148-196`):
```python
async def _run_inference(
    prompt: str,
    *,
    api_key: str,
    history: RunHistory,
    stream_fn: StreamFn = stream_chat_completion,
    strategy: RoutingStrategy = DEFAULT_STRATEGY,
) -> InferenceRun:
    # ...
    try:
        async for event in stream_fn(prompt, strategy=strategy, api_key=api_key):
            if isinstance(event, StreamChunk):
                text_parts.append(event.text_delta)
                continue
            # Process StreamedResult
    except OpenRouterError as exc:
        # Build FAILED InferenceRun
```

**What to implement — `run_fallback_scenario()`:**
- Signature: `async def run_fallback_scenario(prompt, *, fallback_strategy, api_key, stream_fn=stream_chat_completion) -> AsyncIterator[StreamChunk | StreamedResult | FallbackResult]`
- Attempt 1: call `stream_fn` with `FALLBACK_PRIMARY_STRATEGY`, catch `OpenRouterError`, build `AttemptRecord(status=FAILED)`
- Attempt 2: call `stream_fn` with `fallback_strategy`, yield `StreamChunk` events for progressive display, collect `StreamedResult`
- Yield a `FallbackResult` combining both `AttemptRecord` objects
- Use `time.monotonic()` for latency (same as `client.py:99`)

**Imports to add:**
```python
from collections.abc import AsyncIterator
import time
from openrouter_demo.client import OpenRouterError, stream_chat_completion
from openrouter_demo.models import (
    AttemptRecord,
    FallbackEvidence,
    Status,
    StreamChunk,
    StreamedResult,
    UNAVAILABLE,
)
from openrouter_demo.routing import FALLBACK_PRIMARY_STRATEGY, RoutingStrategy
```

**Note:** `PhaseNotImplementedError` class must be preserved — `test_imports.py:25-27` imports it and checks the error message. The `run_scenario` stub function should be replaced with `run_fallback_scenario` but `PhaseNotImplementedError` stays.

---

### `src/openrouter_demo/client.py` (service, streaming) — NO CHANGES

**Analog:** itself

**Why no changes:** `stream_chat_completion` already accepts `strategy: RoutingStrategy | None` and merges `strategy_payload(strategy)` into the request body (line 80-84). When `strategy_payload` is updated to include the `provider` key, it flows through automatically. The `model` parameter also already supports override (line 66-67).

**Key pattern to preserve — error types** (lines 10-29):
```python
class OpenRouterError(Exception):
    def __init__(self, message: str, *, partial_text: str = "") -> None:
        super().__init__(message)
        self.partial_text = partial_text


class OpenRouterHTTPError(OpenRouterError):
    def __init__(self, message, *, status_code, partial_text="", error_payload=None):
        super().__init__(message, partial_text=partial_text)
        self.status_code = status_code
        self.error_payload = error_payload
```

These error types are what `run_fallback_scenario` catches for the primary attempt failure. The `status_code` field on `OpenRouterHTTPError` provides the failure reason for `AttemptRecord.error_message`.

---

### `src/openrouter_demo/ui.py` (component, event-driven)

**Analog:** itself — extend existing handlers and rendering

**Streaming seam pattern** (lines 286-310) — THE critical pattern to preserve:
```python
async def run_request() -> None:
    # ... state setup ...
    state.is_running = True
    state.response = ""
    state.response_status = STREAMING_RESPONSE
    sync_run_button()
    refresh(response_panel)
    refresh(telemetry_panel)

    async def observed_stream(
        prompt_value: str, **kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        async for event in stream_fn(prompt_value, **kwargs):
            if isinstance(event, StreamChunk):
                state.response = state.response + event.text_delta
                refresh(response_panel)
            yield event

    run = await _run_inference(
        prompt_text,
        api_key=os.environ.get(OPENROUTER_API_KEY, ""),
        history=history,
        stream_fn=observed_stream,
        strategy=DEFAULT_STRATEGY,  # <-- THIS becomes strategy selector value
    )
    state.is_running = False
    state.last_run = run
    # ... status + refresh ...
```

**What to change in `run_request()`:**
1. Read strategy from a selector instead of hardcoded `DEFAULT_STRATEGY`
2. Read fallback toggle; if ON, call `run_fallback_scenario` instead of `_run_inference`
3. Handle `FallbackResult` yield from scenario — stream chunks, then build `InferenceRun(status=FALLBACK_SUCCEEDED, fallback_evidence=...)`

**Telemetry rows pattern** (lines 72-105) — extend for fallback:
```python
def _telemetry_rows(run: InferenceRun | None, *, is_running: bool = False) -> list[tuple[str, str]]:
    # ...
    status = SUCCESS_RESPONSE if run.status is Status.SUCCEEDED else FAILURE_RESPONSE
    return [
        ("Status", status),
        ("Strategy", strategy),
        ("Model", _format_metadata(telemetry.model) if telemetry else ...),
        # ...
    ]
```

**What to add:** Handle `Status.FALLBACK_SUCCEEDED` — status copy should be "Completed via fallback route after primary route failed." Add rows for primary model/status and fallback model/status when `run.fallback_evidence` is present.

**History rows pattern** (lines 107-121):
```python
def _history_rows(history: RunHistory) -> list[tuple[str, str, str, str, str, str, str]]:
    for index, run in enumerate(history.all(), start=1):
        rows.append((str(index), run.strategy_name, ...))
```

**What to add:** A "Fallback" column ("Yes" when `run.fallback_evidence is not None`, "—" otherwise). This changes the tuple length from 7 to 8 — update the `columns` tuple in `_render_history` (line 131) and the grid columns count accordingly.

**UI control pattern** (lines 355-366) — for strategy selector:
```python
with ui.card().classes("w-full"):
    ui.label("Prompt").classes("font-semibold")
    prompt = ui.textarea(...)
    # ...
    ui.label("Default").classes("font-semibold")
    ui.label(DEFAULT_STRATEGY.description).classes("text-sm text-gray-600")
    run_button = ui.button("Run Inference", on_click=run_request)
```

**What to add:** Replace the hardcoded "Default" label with a `ui.select` bound to strategy registry, showing the selected strategy's `description` below it. Add a `ui.switch` or `ui.checkbox` for the fallback toggle. Reference screen spec for exact copy.

**Format helpers** (lines 34-53) — reuse, do not duplicate:
```python
def _format_metadata(value: str | Unavailable) -> str: ...
def _format_tokens(value: int | Unavailable) -> str: ...
def _format_latency(value: int | Unavailable) -> str: ...
def _format_cost(value: float | Unavailable) -> str: ...
```

Fallback evidence rendering must use these same helpers — never stringify `UNAVAILABLE` directly.

---

### `src/openrouter_demo/history.py` (store, CRUD) — NO CHANGES

**Analog:** itself

**Why no changes:** `RunHistory` stores `InferenceRun` objects. Since `InferenceRun` gains `fallback_evidence` as a field with a default, existing `append(run)` and `all()` work unchanged. The UI extracts `fallback_evidence` during rendering.

**Pattern to preserve** (lines 1-15):
```python
class RunHistory:
    def __init__(self, max_runs: int = 50) -> None:
        self._max_runs = max_runs
        self._runs: list[InferenceRun] = []

    def append(self, run: InferenceRun) -> None:
        self._runs.append(run)
        if len(self._runs) > self._max_runs:
            self._runs = self._runs[-self._max_runs :]

    def all(self) -> list[InferenceRun]:
        return list(self._runs)
```

---

### `tests/test_routing.py` (test, request-response) — NEW FILE

**Analog:** `tests/test_client.py` (assertion style, no live calls)

**Test structure pattern** (from `test_client.py:1-14`):
```python
import json
import httpx
import pytest
from openrouter_demo.routing import DEFAULT_STRATEGY, strategy_payload, COST_STRATEGY, LATENCY_STRATEGY
```

**What to test:**
1. `strategy_payload(DEFAULT_STRATEGY)` returns `{"model": "openai/gpt-4o-mini"}` with no `provider` key
2. `strategy_payload(COST_STRATEGY)` returns `{"model": ..., "provider": {"sort": "price"}}`
3. `strategy_payload(LATENCY_STRATEGY)` returns `{"model": ..., "provider": {"sort": "latency"}}`
4. `strategy_payload(FALLBACK_PRIMARY_STRATEGY)` returns `{"model": "nonexistent/...", "provider": {"allow_fallbacks": False}}`
5. `ROUTING_STRATEGY_LABELS` unchanged (already covered in `test_imports.py` — don't duplicate)

**Assertion style** — plain `assert`, no `self.assertEqual`:
```python
def test_cost_strategy_payload_includes_price_sort() -> None:
    payload = strategy_payload(COST_STRATEGY)
    assert payload["model"] == "openai/gpt-4o-mini"
    assert payload["provider"] == {"sort": "price"}
```

---

### `tests/test_scenarios.py` (test, streaming) — NEW FILE

**Analog:** `tests/test_ui.py` (injected async streams, no network)

**Injected stream pattern** (from `test_ui.py:17-26`):
```python
async def fake_stream(*_args: object, **_kwargs: object) -> AsyncIterator[StreamChunk | StreamedResult]:
    yield StreamChunk("Hello ")
    yield StreamChunk("there")
    yield StreamedResult(
        text="Hello there",
        model="openai/gpt-4o-mini",
        provider="OpenAI",
        prompt_tokens=3, completion_tokens=4, total_tokens=7,
        cost_usd=0.001, latency_ms=321,
    )
```

**Error injection pattern** (from `test_ui.py:73-76`):
```python
async def fake_stream(*_args: object, **_kwargs: object) -> AsyncIterator[StreamChunk | StreamedResult]:
    yield StreamChunk("partial")
    raise OpenRouterHTTPError("provider failed", status_code=500, partial_text="partial")
```

**What to test in `test_scenarios.py`:**
1. Primary fails (404) → fallback succeeds → `FallbackResult` has both `AttemptRecord`s, primary `status=FAILED`, fallback `status=SUCCEEDED`
2. Primary fails → `AttemptRecord.error_message` contains the error string, `latency_ms` is a non-negative int
3. Primary unexpectedly succeeds → edge case handling (yield early or treat as normal)
4. Fallback stream chunks are yielded progressively (collect them and assert order)
5. Use two separate injected streams: one that raises `OpenRouterHTTPError(status_code=404)`, one that yields chunks + `StreamedResult`

**Pattern for distinguishing which call gets which stream:**
```python
call_count = 0

async def dual_stream(*_args, **kwargs) -> AsyncIterator[...]:
    nonlocal call_count
    call_count += 1
    if call_count == 1:
        raise OpenRouterHTTPError("Model not found", status_code=404, partial_text="")
    yield StreamChunk("Fallback ")
    yield StreamedResult(text="Fallback response", ...)
```

**Run pattern** — use `asyncio.run()`:
```python
def _run(coro):
    return asyncio.run(coro)
```

---

### `tests/test_ui.py` (test, event-driven) — EXTEND

**Analog:** itself

**What to add:**
1. Test that `_run_inference` (or new fallback handler) with a fallback stream produces `Status.FALLBACK_SUCCEEDED` and `fallback_evidence` is not None
2. Test that `_telemetry_rows` with a fallback run shows fallback-specific status copy
3. Test that `_history_rows` includes the "Fallback" column ("Yes" for fallback runs, "—" for normal runs)
4. Test that strategy selector value flows through to `run.strategy_name` (inject a stream that checks `kwargs["strategy"].name`)

**Existing pattern to follow** (from `test_ui.py:28-42`):
```python
history = RunHistory()
run = _run(_run_inference("Explain streaming", api_key="sk-test", history=history, stream_fn=fake_stream))

assert run.status is Status.SUCCEEDED
assert run.streamed_text == "Hello there"
assert run.strategy_name == DEFAULT_STRATEGY.name
assert run.telemetry is not None
assert history.all() == [run]
```

---

### `tests/test_imports.py` (test, request-response) — EXTEND

**Analog:** itself

**What to change:**
1. Line 25-27: `test_live_boundaries_raise_honest_phase_errors` — update `run_scenario` expectation. Either remove the `run_scenario` assertion (if the function is replaced) or update it to check that `run_fallback_scenario` is now importable and `PhaseNotImplementedError` still exists for evals.
2. Add assertions that new types are importable: `AttemptRecord`, `FallbackEvidence`, `Status.FALLBACK_SUCCEEDED`, `COST_STRATEGY`, `LATENCY_STRATEGY`, `FALLBACK_PRIMARY_STRATEGY`
3. Do NOT change `test_routing_labels_do_not_claim_provider_results` (lines 46-51) — the labels dict stays the same.

**Existing import verification pattern** (lines 11-26):
```python
def test_required_modules_import() -> None:
    for name in ("openrouter_demo", "openrouter_demo.client", ...):
        assert importlib.import_module(name)
```

**What to add:**
```python
from openrouter_demo.models import AttemptRecord, FallbackEvidence, Status
from openrouter_demo.routing import COST_STRATEGY, LATENCY_STRATEGY, FALLBACK_PRIMARY_STRATEGY

def test_phase3_types_import() -> None:
    assert hasattr(Status, "FALLBACK_SUCCEEDED")
    assert COST_STRATEGY.name == "cost"
    assert LATENCY_STRATEGY.name == "latency"
    assert FALLBACK_PRIMARY_STRATEGY.provider_preferences == {"allow_fallbacks": False}
```

## Shared Patterns

### UNAVAILABLE Sentinel Handling
**Source:** `src/openrouter_demo/models.py:5-12`
**Apply to:** `scenarios.py` (primary attempt telemetry), `ui.py` (fallback evidence rendering), `test_scenarios.py`, `test_ui.py`
```python
@dataclass(frozen=True)
class Unavailable:
    label: str = "unavailable"
    def __bool__(self) -> bool:
        return False

UNAVAILABLE = Unavailable()
```
**Rule:** Failed primary attempt has `provider=UNAVAILABLE`, tokens=UNAVAILABLE, cost=UNAVAILABLE. These must remain as `UNAVAILABLE` sentinels until rendered by `_format_metadata`/`_format_tokens`/`_format_cost`. Never coerce to `0`, `""`, or `None`.

### Injected Async Streams (No-Network Tests)
**Source:** `tests/test_ui.py:17-26`, `tests/test_client.py:14-19`
**Apply to:** `tests/test_scenarios.py`, extended `tests/test_ui.py`
```python
async def fake_stream(*_args: object, **_kwargs: object) -> AsyncIterator[StreamChunk | StreamedResult]:
    yield StreamChunk("Hello ")
    yield StreamedResult(text="Hello there", model="openai/gpt-4o-mini", ...)

# Error injection:
async def failing_stream(*_args, **_kwargs) -> AsyncIterator[...]:
    raise OpenRouterHTTPError("Model not found", status_code=404, partial_text="")
```
**Rule:** No test instantiates `httpx.AsyncClient` or calls live OpenRouter. All streams are injected via `stream_fn` parameter.

### Frozen Dataclass with Default Fields
**Source:** `src/openrouter_demo/models.py` (all types), `src/openrouter_demo/config.py`
**Apply to:** `models.py` new types (`AttemptRecord`, `FallbackEvidence`)
```python
@dataclass(frozen=True)
class NewType:
    field: str | Unavailable
    optional_with_default: FallbackEvidence | None = None
```
**Rule:** All new types are `frozen=True`. New fields on existing types get defaults at the END to preserve positional-arg compatibility.

### Streaming Seam in UI State
**Source:** `src/openrouter_demo/ui.py:286-310`
**Apply to:** Extended `run_request()` for fallback path
```python
async def observed_stream(prompt_value, **kwargs) -> AsyncIterator[...]:
    async for event in stream_fn(prompt_value, **kwargs):
        if isinstance(event, StreamChunk):
            state.response += event.text_delta
            refresh(response_panel)
        yield event
```
**Rule:** UI owns progressive display. The stream function is always injectable. Fallback scenario yields chunks through the same `observed_stream` wrapper.

### Error Type Hierarchy
**Source:** `src/openrouter_demo/client.py:10-29`
**Apply to:** `scenarios.py` (catches `OpenRouterError` for primary attempt)
```python
class OpenRouterError(Exception):
    def __init__(self, message, *, partial_text=""): ...

class OpenRouterHTTPError(OpenRouterError):
    def __init__(self, message, *, status_code, partial_text="", error_payload=None): ...
    self.status_code = status_code
```
**Rule:** `scenarios.py` catches `OpenRouterError` (parent) to handle all failure modes. `OpenRouterHTTPError.status_code` provides the HTTP reason for `AttemptRecord.error_message`.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | — | — | All files have close analogs in the existing codebase |

**Note:** `tests/test_routing.py` and `tests/test_scenarios.py` are new files but have strong analogs (`test_client.py` and `test_ui.py` respectively). `scenarios.py` is transformed from a stub to a real service but follows the established async-generator + stream-consumption patterns from `client.py` and `ui.py:_run_inference`.

## Metadata

**Analog search scope:** `src/openrouter_demo/*.py`, `tests/*.py`, `app.py`
**Files scanned:** 14 source + test files
**Pattern extraction date:** 2026-08-19