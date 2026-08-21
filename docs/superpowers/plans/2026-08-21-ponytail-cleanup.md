# Ponytail Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove dead/speculative code and shrink redundant wrappers identified by a ponytail-audit pass, without changing any observable behavior.

**Architecture:** Each task deletes or shrinks one cohesive piece of dead/redundant code and updates the tests that reference it. Tasks are ordered so no task depends on a later one; several touch the same files (`models.py`, `ui.py`) but each is independently committable and independently revertable.

**Tech Stack:** Python 3.13, pytest, stdlib only (this plan *removes* code, it adds none).

**Spec:** No separate spec document — the approved cleanup list is the task list below. It was audited against the codebase before planning; one originally-proposed item (deleting `STRATEGY_MODELS`/`STRATEGY_MODEL_SHORT_NAMES` in `ui.py` as a "duplicate" of `RoutingStrategy.model`) was dropped after verification showed the values genuinely differ (`COST_STRATEGY.model` is `openai/gpt-4o-mini`, but `STRATEGY_MODELS["cost"]` — the value actually used at runtime — is `openai/gpt-oss-20b:free`). Deleting it would have silently changed which model the cost strategy calls. That item is **not** part of this plan.

## Global Constraints

- No behavior change. Every task must leave `pytest` green with the same pass/fail semantics as before the task, minus the assertions that specifically tested the deleted code's existence.
- Delete test coverage for deleted code; do not leave orphaned imports or dead assertions.
- No new abstractions, no backwards-compat shims (e.g. no re-exporting deleted names).
- Commit after each task.

---

### Task 1: Delete `scenarios.py` and its dead `StreamFn` alias

**Files:**
- Delete: `src/openrouter_demo/scenarios.py`
- Modify: `tests/test_imports.py`
- Modify: `tests/test_phase1_guards.py`

**Interfaces:**
- Consumes: nothing (this module is imported by nothing in `src/`; `ui.py` and `evals.py` each already define their own local `type StreamFn = Callable[..., AsyncIterator[StreamChunk | StreamedResult]]` and are untouched by this task).
- Produces: nothing later depends on this task.

- [ ] **Step 1: Remove references to the module from tests**

In `tests/test_imports.py`, remove this line from the `for name in (...)` tuple in `test_required_modules_import`:

```python
        "openrouter_demo.scenarios",
```

In `tests/test_phase1_guards.py`, remove this line from `core_modules` in `test_phase1_keeps_langfuse_tracing_isolated_to_telemetry`:

```python
        Path("src/openrouter_demo/scenarios.py"),
```

- [ ] **Step 2: Delete the file**

```bash
rm src/openrouter_demo/scenarios.py
```

- [ ] **Step 3: Run tests to verify green**

Run: `pytest tests/test_imports.py tests/test_phase1_guards.py -v`
Expected: PASS, no `ModuleNotFoundError`, no leftover path assertion failures.

- [ ] **Step 4: Commit**

```bash
git add -A src/openrouter_demo/scenarios.py tests/test_imports.py tests/test_phase1_guards.py
git commit -m "chore: delete unused scenarios.py module"
```

---

### Task 2: Delete unused `Status` enum members

**Files:**
- Modify: `src/openrouter_demo/models.py:31-38`

**Interfaces:**
- Consumes: nothing.
- Produces: `Status` retains `SUCCEEDED`, `FALLBACK_SUCCEEDED`, `FAILED` — the only members any code reads (confirmed via grep: no test or src file references `Status.PENDING`, `Status.STREAMING`, or `Status.CANCELLED`, or their string values `"pending"`/`"streaming"`/`"cancelled"`).

- [ ] **Step 1: Remove the unused members**

Replace in `src/openrouter_demo/models.py`:

```python
class Status(StrEnum):
    PENDING = "pending"
    STREAMING = "streaming"
    SUCCEEDED = "succeeded"
    FALLBACK_SUCCEEDED = "fallback_succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

with:

```python
class Status(StrEnum):
    SUCCEEDED = "succeeded"
    FALLBACK_SUCCEEDED = "fallback_succeeded"
    FAILED = "failed"
```

- [ ] **Step 2: Run tests to verify green**

Run: `pytest -v`
Expected: PASS (no test constructs `Status.PENDING`/`STREAMING`/`CANCELLED`).

- [ ] **Step 3: Commit**

```bash
git add src/openrouter_demo/models.py
git commit -m "chore: remove unused Status enum members"
```

---

### Task 3: Delete `Unavailable.__bool__`

**Files:**
- Modify: `src/openrouter_demo/models.py:6-11`
- Modify: `tests/test_imports.py`
- Modify: `tests/test_telemetry.py`
- Modify: `tests/test_client.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Unavailable` becomes a plain frozen dataclass with default truthiness (`True`). Every production code path already checks `isinstance(x, Unavailable)` rather than truthiness (confirmed via grep — the only `not <Unavailable-typed-value>` usages are in the three test files below).

- [ ] **Step 1: Remove the dunder method**

Replace in `src/openrouter_demo/models.py`:

```python
@dataclass(frozen=True)
class Unavailable:
    label: str = "unavailable"

    def __bool__(self) -> bool:
        return False
```

with:

```python
@dataclass(frozen=True)
class Unavailable:
    label: str = "unavailable"
```

- [ ] **Step 2: Update the three tests that relied on falsy `Unavailable`**

In `tests/test_imports.py`, in `test_unavailable_metadata_is_not_zero`, remove this line:

```python
    assert not UNAVAILABLE
```

(leaving `assert isinstance(UNAVAILABLE, Unavailable)` and `assert UNAVAILABLE != 0`.)

In `tests/test_telemetry.py`, in `test_unavailable_sentinel_is_not_zero_or_dict`, remove this line:

```python
    assert not UNAVAILABLE
```

(leaving `assert isinstance(UNAVAILABLE, Unavailable)` and `assert UNAVAILABLE != 0`.)

In `tests/test_client.py`, in `test_stream_missing_usage_is_unavailable`, replace:

```python
    assert not result.prompt_tokens
    assert result.prompt_tokens != 0
```

with:

```python
    assert isinstance(result.prompt_tokens, Unavailable)
    assert result.prompt_tokens != 0
```

and add `Unavailable` to the existing import in `tests/test_client.py`:

```python
from openrouter_demo.models import UNAVAILABLE, StreamChunk, StreamedResult, Unavailable
```

- [ ] **Step 3: Run tests to verify green**

Run: `pytest tests/test_imports.py tests/test_telemetry.py tests/test_client.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add src/openrouter_demo/models.py tests/test_imports.py tests/test_telemetry.py tests/test_client.py
git commit -m "chore: remove unused Unavailable.__bool__"
```

---

### Task 4: Delete `AttemptRecord`, `FallbackEvidence`, `RepeatObservation` and their sqlite round-trip helpers

**Files:**
- Modify: `src/openrouter_demo/models.py:165-207`
- Modify: `src/openrouter_demo/sqlite_store.py`
- Modify: `tests/test_imports.py`
- Modify: `tests/test_routing.py`
- Delete: `tests/test_sqlite_store.py` (entirely — every test in this file exercises only the three speculative types being deleted)

**Interfaces:**
- Consumes: nothing (nothing in `src/` ever constructs `AttemptRecord`, `FallbackEvidence`, or `RepeatObservation` — `InferenceRun.fallback_evidence`/`.repeat_observation` are always `None` in every construction site in `ui.py` and `evals.py`).
- Produces: `InferenceRun` keeps `run_id`, `prompt`, `strategy_name`, `started_at`, `completed_at`, `status`, `streamed_text`, `error_message`, `telemetry`. `SQLiteRunHistory.append`/`.all`/`.get` keep their existing signatures, only the payload shape they serialize/deserialize shrinks.

- [ ] **Step 1: Remove the dataclasses and the two `InferenceRun` fields from `models.py`**

Delete this block (currently `models.py:165-192`):

```python
@dataclass(frozen=True)
class AttemptRecord:
    model: str | Unavailable
    provider: str | Unavailable
    status: Status
    error_message: str | None
    latency_ms: int
    prompt_tokens: int | Unavailable
    completion_tokens: int | Unavailable
    total_tokens: int | Unavailable
    cost_usd: float | Unavailable


@dataclass(frozen=True)
class FallbackEvidence:
    primary: AttemptRecord
    fallback: AttemptRecord
    simulated: bool


@dataclass(frozen=True)
class RepeatObservation:
    first: StreamedResult
    second: StreamedResult
    cache_status: str | Unavailable
    cached_tokens: int | Unavailable
    cache_write_tokens: int | Unavailable
```

Replace the `InferenceRun` dataclass (currently `models.py:194-207`):

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
    fallback_evidence: FallbackEvidence | None = None
    repeat_observation: RepeatObservation | None = None
```

with:

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

- [ ] **Step 2: Simplify `sqlite_store.py`**

Replace the import block:

```python
from openrouter_demo.models import (
    AttemptRecord,
    FallbackEvidence,
    InferenceRun,
    RepeatObservation,
    Status,
    StreamedResult,
    TelemetryEvidence,
    deserialize_value,
)
```

with:

```python
from openrouter_demo.models import (
    InferenceRun,
    Status,
    TelemetryEvidence,
)
```

Delete the three helper functions `_attempt_from_dict`, `_streamed_result_from_dict`, `_fallback_evidence_from_dict`, `_repeat_observation_from_dict` (lines 20-66).

In `append`, replace:

```python
    def append(self, run: InferenceRun) -> None:
        payload = {
            "telemetry": run.telemetry.to_dict() if run.telemetry is not None else None,
            "fallback_evidence": asdict(run.fallback_evidence)
            if run.fallback_evidence is not None
            else None,
            "repeat_observation": asdict(run.repeat_observation)
            if run.repeat_observation is not None
            else None,
        }
        telemetry_json = json.dumps(payload)
```

with:

```python
    def append(self, run: InferenceRun) -> None:
        payload = {
            "telemetry": run.telemetry.to_dict() if run.telemetry is not None else None,
        }
        telemetry_json = json.dumps(payload)
```

Remove the now-unused `asdict` import (`from dataclasses import asdict`).

In `_row_to_run`, replace:

```python
    def _row_to_run(self, row: sqlite3.Row) -> InferenceRun:
        telemetry = None
        fallback_evidence = None
        repeat_observation = None
        if row["telemetry_json"]:
            doc = json.loads(row["telemetry_json"])
            if isinstance(doc, dict) and "telemetry" in doc:
                if doc.get("telemetry") is not None:
                    telemetry = TelemetryEvidence.from_dict(doc["telemetry"])
                if doc.get("fallback_evidence") is not None:
                    fallback_evidence = _fallback_evidence_from_dict(doc["fallback_evidence"])
                if doc.get("repeat_observation") is not None:
                    repeat_observation = _repeat_observation_from_dict(doc["repeat_observation"])
        started_at = datetime.fromisoformat(row["started_at"]) if row["started_at"] else None
        completed_at = datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
        status = Status(row["status"]) if row["status"] else Status.FAILED
        return InferenceRun(
            run_id=row["run_id"],
            prompt=row["prompt"],
            strategy_name=row["strategy_name"],
            started_at=started_at,
            completed_at=completed_at,
            status=status,
            streamed_text=row["streamed_text"],
            error_message=row["error_message"],
            telemetry=telemetry,
            fallback_evidence=fallback_evidence,
            repeat_observation=repeat_observation,
        )
```

with:

```python
    def _row_to_run(self, row: sqlite3.Row) -> InferenceRun:
        telemetry = None
        if row["telemetry_json"]:
            doc = json.loads(row["telemetry_json"])
            if isinstance(doc, dict) and doc.get("telemetry") is not None:
                telemetry = TelemetryEvidence.from_dict(doc["telemetry"])
        started_at = datetime.fromisoformat(row["started_at"]) if row["started_at"] else None
        completed_at = datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
        status = Status(row["status"]) if row["status"] else Status.FAILED
        return InferenceRun(
            run_id=row["run_id"],
            prompt=row["prompt"],
            strategy_name=row["strategy_name"],
            started_at=started_at,
            completed_at=completed_at,
            status=status,
            streamed_text=row["streamed_text"],
            error_message=row["error_message"],
            telemetry=telemetry,
        )
```

- [ ] **Step 3: Update tests**

Delete `tests/test_sqlite_store.py` entirely — every one of its three tests constructs `AttemptRecord`/`FallbackEvidence`/`RepeatObservation` to assert round-trip persistence of fields that no longer exist.

```bash
rm tests/test_sqlite_store.py
```

In `tests/test_imports.py`:
- Change the import line from:
  ```python
  from openrouter_demo.models import UNAVAILABLE, AttemptRecord, FallbackEvidence, Status, Unavailable
  ```
  to:
  ```python
  from openrouter_demo.models import UNAVAILABLE, Status, Unavailable
  ```
- In `test_phase3_types_importable`, remove:
  ```python
      assert AttemptRecord is not None
      assert FallbackEvidence is not None
  ```
- In `test_phase4_types_and_fields_importable`, remove `RepeatObservation` from the import and the assertion:
  ```python
      from openrouter_demo.models import RepeatObservation, TelemetryEvidence
      from openrouter_demo.telemetry import TraceOutcome

      assert RepeatObservation is not None
      assert TraceOutcome is not None
  ```
  becomes:
  ```python
      from openrouter_demo.models import TelemetryEvidence
      from openrouter_demo.telemetry import TraceOutcome

      assert TraceOutcome is not None
  ```

In `tests/test_routing.py`:
- Change the import line from:
  ```python
  from openrouter_demo.models import UNAVAILABLE, AttemptRecord, FallbackEvidence, Status
  ```
  to:
  ```python
  from openrouter_demo.models import Status
  ```
  (Task 5 below removes the `UNAVAILABLE` usage's only remaining call site in this file — see that task; if Task 5 has not yet run, leave `UNAVAILABLE` in the import for now and let Task 5 drop it.)
- Delete `test_attempt_record_is_frozen_dataclass` and `test_fallback_evidence_is_frozen_dataclass` in full (lines 45-105) — they test only the deleted types.

- [ ] **Step 4: Run tests to verify green**

Run: `pytest -v`
Expected: PASS, no `ImportError` for the deleted names.

- [ ] **Step 5: Commit**

```bash
git add src/openrouter_demo/models.py src/openrouter_demo/sqlite_store.py tests/test_imports.py tests/test_routing.py
git rm tests/test_sqlite_store.py
git commit -m "chore: delete unused AttemptRecord/FallbackEvidence/RepeatObservation types"
```

---

### Task 5: Delete `FALLBACK_PRIMARY_STRATEGY`

**Files:**
- Modify: `src/openrouter_demo/routing.py:41-46`
- Modify: `tests/test_imports.py`
- Modify: `tests/test_routing.py`

**Interfaces:**
- Consumes: nothing in `src/` references `FALLBACK_PRIMARY_STRATEGY` — only test files do.
- Produces: nothing later depends on it.

- [ ] **Step 1: Remove the strategy constant from `routing.py`**

Delete:

```python
FALLBACK_PRIMARY_STRATEGY = RoutingStrategy(
    name="custom",
    description="Simulated primary route failure for demo fallback scenario.",
    model="nonexistent/fake-model-for-demo",
    provider_preferences={"allow_fallbacks": False},
)

```

(the blank line immediately after it, before `STRATEGIES: dict[...]`, stays.)

- [ ] **Step 2: Update tests**

In `tests/test_imports.py`:
- Remove `FALLBACK_PRIMARY_STRATEGY,` from the `from openrouter_demo.routing import (...)` block.
- In `test_phase3_types_importable`, remove:
  ```python
      assert FALLBACK_PRIMARY_STRATEGY.name == "custom"
  ```

In `tests/test_routing.py`:
- Remove `FALLBACK_PRIMARY_STRATEGY,` from the `from openrouter_demo.routing import (...)` block. Also drop `UNAVAILABLE` from the `openrouter_demo.models` import (its only two call sites were inside the two tests Task 4 already deleted) — the import line becomes just:
  ```python
  from openrouter_demo.models import Status
  ```
- Delete `test_fallback_primary_strategy_payload_includes_allow_fallbacks_false` in full (lines 29-32).

- [ ] **Step 3: Run tests to verify green**

Run: `pytest tests/test_imports.py tests/test_routing.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add src/openrouter_demo/routing.py tests/test_imports.py tests/test_routing.py
git commit -m "chore: delete unused FALLBACK_PRIMARY_STRATEGY"
```

---

### Task 6: Simplify the `OpenRouterError` hierarchy

**Files:**
- Modify: `src/openrouter_demo/client.py`
- Modify: `tests/test_client.py`
- Modify: `tests/test_ui.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `OpenRouterError(message, *, partial_text="")` and `OpenRouterHTTPError(message, *, partial_text="")` remain the only two exception types raised by `stream_chat_completion`. Every caller in `ui.py` and `evals.py` already catches only `OpenRouterError` (its base), so this is a pure narrowing of the raise sites.

- [ ] **Step 1: Remove the subclasses and the unused attrs in `client.py`**

Replace:

```python
class OpenRouterError(Exception):
    def __init__(self, message: str, *, partial_text: str = "") -> None:
        super().__init__(message)
        self.partial_text = partial_text


class OpenRouterAuthError(OpenRouterError):
    pass


class OpenRouterHTTPError(OpenRouterError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        partial_text: str = "",
        error_payload: dict | None = None,
    ) -> None:
        super().__init__(message, partial_text=partial_text)
        self.status_code = status_code
        self.error_payload = error_payload


class OpenRouterTimeoutError(OpenRouterError):
    pass
```

with:

```python
class OpenRouterError(Exception):
    def __init__(self, message: str, *, partial_text: str = "") -> None:
        super().__init__(message)
        self.partial_text = partial_text


class OpenRouterHTTPError(OpenRouterError):
    pass
```

- [ ] **Step 2: Update the three raise sites in `stream_chat_completion`**

Replace:

```python
                if response.status_code == 401:
                    partial = "".join(text_parts)
                    raise OpenRouterAuthError(
                        f"OpenRouter auth failed ({response.status_code})", partial_text=partial
                    )
                if response.status_code >= 400:
                    partial = "".join(text_parts)
                    raise OpenRouterHTTPError(
                        f"OpenRouter request failed ({response.status_code})",
                        status_code=response.status_code,
                        partial_text=partial,
                    )
```

with:

```python
                if response.status_code == 401:
                    partial = "".join(text_parts)
                    raise OpenRouterHTTPError(
                        f"OpenRouter auth failed ({response.status_code})", partial_text=partial
                    )
                if response.status_code >= 400:
                    partial = "".join(text_parts)
                    raise OpenRouterHTTPError(
                        f"OpenRouter request failed ({response.status_code})",
                        partial_text=partial,
                    )
```

Replace:

```python
                    if isinstance(payload, dict) and "error" in payload:
                        err = payload["error"]
                        err_obj = err if isinstance(err, dict) else {"message": str(err) if err is not None else None}
                        msg = err_obj.get("message")
                        partial = "".join(text_parts)
                        raise OpenRouterHTTPError(
                            str(msg) if msg else "OpenRouter error",
                            status_code=response.status_code,
                            partial_text=partial,
                            error_payload=err_obj,
                        )
```

with:

```python
                    if isinstance(payload, dict) and "error" in payload:
                        err = payload["error"]
                        err_obj = err if isinstance(err, dict) else {"message": str(err) if err is not None else None}
                        msg = err_obj.get("message")
                        partial = "".join(text_parts)
                        raise OpenRouterHTTPError(
                            str(msg) if msg else "OpenRouter error",
                            partial_text=partial,
                        )
```

Replace:

```python
        except OpenRouterError:
            raise
        except httpx.TimeoutException as exc:
            partial = "".join(text_parts)
            raise OpenRouterTimeoutError(f"OpenRouter request timed out: {exc}", partial_text=partial) from exc
        except httpx.HTTPError as exc:
            partial = "".join(text_parts)
            # already handled status codes above; treat as generic HTTP error, but
            # surface a status code when one is attached to the underlying response.
            status_code = exc.response.status_code if exc.response is not None else 0
            raise OpenRouterHTTPError(str(exc), status_code=status_code, partial_text=partial) from exc
```

with:

```python
        except OpenRouterError:
            raise
        except httpx.TimeoutException as exc:
            partial = "".join(text_parts)
            raise OpenRouterHTTPError(f"OpenRouter request timed out: {exc}", partial_text=partial) from exc
        except httpx.HTTPError as exc:
            partial = "".join(text_parts)
            raise OpenRouterHTTPError(str(exc), partial_text=partial) from exc
```

- [ ] **Step 3: Update tests**

In `tests/test_client.py`:
- Change the import from:
  ```python
  from openrouter_demo.client import (
      OpenRouterAuthError,
      OpenRouterHTTPError,
      stream_chat_completion,
  )
  ```
  to:
  ```python
  from openrouter_demo.client import (
      OpenRouterHTTPError,
      stream_chat_completion,
  )
  ```
- In `test_stream_401_raises_auth_error`, change:
  ```python
      with pytest.raises(OpenRouterAuthError):
          asyncio.run(_run())
  ```
  to:
  ```python
      with pytest.raises(OpenRouterHTTPError):
          asyncio.run(_run())
  ```

In `tests/test_ui.py`, in `test_run_inference_records_partial_text_on_stream_failure`, change:

```python
        raise OpenRouterHTTPError("provider failed", status_code=500, partial_text="partial")
```

to:

```python
        raise OpenRouterHTTPError("provider failed", partial_text="partial")
```

- [ ] **Step 4: Run tests to verify green**

Run: `pytest tests/test_client.py tests/test_ui.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/openrouter_demo/client.py tests/test_client.py tests/test_ui.py
git commit -m "chore: collapse OpenRouterError hierarchy to the two types callers actually catch"
```

---

### Task 7: Delete `_format_metadata` and `_format_cost` dead wrappers in `ui.py`

**Files:**
- Modify: `src/openrouter_demo/ui.py:607-612`
- Modify: `tests/test_ui.py`

**Interfaces:**
- Consumes: nothing (zero call sites in `ui.py` itself — only `tests/test_ui.py` calls them directly).
- Produces: nothing later depends on them; `formatting.format_trace`/`formatting.format_cost` remain available and already have the behavior these wrappers exposed.

- [ ] **Step 1: Delete the two functions**

Remove from `src/openrouter_demo/ui.py`:

```python
def _format_metadata(value: str | Unavailable) -> str:
    return format_trace(value, unavailable=_UNAVAILABLE_COPY)


def _format_cost(value: float | Unavailable) -> str:
    return format_cost(value, unavailable=_COST_UNAVAILABLE_COPY)


```

- [ ] **Step 2: Update the test to call the underlying formatters directly**

In `tests/test_ui.py`, change the import:

```python
from openrouter_demo.ui import (
    EVAL_DESCRIPTION,
    SAMPLE_PROMPTS,
    STRATEGY_MODELS,
    _format_cost,
    _format_metadata,
    _run_inference,
    _strategy_with_model,
)
```

to:

```python
from openrouter_demo.formatting import format_cost, format_trace
from openrouter_demo.ui import (
    EVAL_DESCRIPTION,
    SAMPLE_PROMPTS,
    STRATEGY_MODELS,
    _COST_UNAVAILABLE_COPY,
    _UNAVAILABLE_COPY,
    _run_inference,
    _strategy_with_model,
)
```

In `test_run_inference_preserves_unavailable_metadata`, change:

```python
    assert _format_metadata(UNAVAILABLE) == "Unavailable from selected route/provider."
    assert _format_cost(UNAVAILABLE) == "Cost metadata was not returned for this route/provider."
```

to:

```python
    assert format_trace(UNAVAILABLE, unavailable=_UNAVAILABLE_COPY) == "Unavailable from selected route/provider."
    assert format_cost(UNAVAILABLE, unavailable=_COST_UNAVAILABLE_COPY) == "Cost metadata was not returned for this route/provider."
```

- [ ] **Step 3: Run tests to verify green**

Run: `pytest tests/test_ui.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add src/openrouter_demo/ui.py tests/test_ui.py
git commit -m "chore: delete unused _format_metadata/_format_cost wrappers"
```

---

### Task 8: Replace hand-rolled `_html_escape` with `html.escape`

**Files:**
- Modify: `src/openrouter_demo/ui.py`

**Interfaces:**
- Consumes: nothing.
- Produces: every call site (`ui.py:876, 881, 896, 897, 899, 901, 902, 907, 910`) keeps calling a function named `_html_escape`, now a one-line wrapper over `html.escape`, so no call site needs editing.

`html.escape` escapes `&`, `<`, `>`, `"`, and (with `quote=True`, the default) `'` — the same five characters the hand-rolled version escaped, in the same left-to-right order dependency (it escapes `&` first internally). Output is identical for all inputs used here (plain strings: model names, params, ids, timestamps).

- [ ] **Step 1: Add the `html` import**

At the top of `src/openrouter_demo/ui.py`, add to the stdlib import group:

```python
import html
```

- [ ] **Step 2: Replace the function body**

Replace:

```python
def _html_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
```

with:

```python
def _html_escape(value: str) -> str:
    return html.escape(value)
```

- [ ] **Step 3: Run tests to verify green**

Run: `pytest tests/test_ui.py -v`
Expected: PASS (all `demo-scores-table` rendering tests still find the same escaped text since output is byte-identical).

- [ ] **Step 4: Commit**

```bash
git add src/openrouter_demo/ui.py
git commit -m "refactor: use stdlib html.escape instead of hand-rolled entity escaping"
```

---

### Task 9: Inline the four `_fmt_*` wrappers in `evals.py`

**Files:**
- Modify: `src/openrouter_demo/evals.py:200-318`

**Interfaces:**
- Consumes: `format_cost`, `format_number`, `format_latency`, `format_trace` — already imported at the top of `evals.py` from `openrouter_demo.formatting`.
- Produces: `format_summary` output is byte-identical; no other module imports the `_fmt_*` names (confirmed via grep — they have no external call sites).

- [ ] **Step 1: Delete the four wrapper functions**

Remove:

```python
def _fmt_cost(value: float | Unavailable | None) -> str:
    return format_cost(value, unavailable="unavailable")


def _fmt_num(value: float | Unavailable | None) -> str:
    return format_number(value, unavailable="unavailable")


def _fmt_latency(value: float | Unavailable | None) -> str:
    return format_latency(value, unavailable="unavailable")


def _fmt_trace(value: str | Unavailable | None) -> str:
    return format_trace(value, unavailable="unavailable")


```

- [ ] **Step 2: Inline the calls in `format_summary`**

Replace:

```python
        lines.append(
            f"{name}: {agg['passed']}/{agg['total']} passed, "
            f"cost {_fmt_cost(agg['total_cost'])}, "
            f"mean latency {_fmt_latency(agg['mean_latency'])}, "
            f"trace {agg['trace_state']}"
        )
```

with:

```python
        lines.append(
            f"{name}: {agg['passed']}/{agg['total']} passed, "
            f"cost {format_cost(agg['total_cost'], unavailable='unavailable')}, "
            f"mean latency {format_latency(agg['mean_latency'], unavailable='unavailable')}, "
            f"trace {agg['trace_state']}"
        )
```

Replace:

```python
    for result in summary.results:
        if result.telemetry is not None:
            lines.append(
                f"{result.case_id} {result.strategy_name}: "
                f"{'pass' if result.passed else 'fail'} — {result.score_reason} | "
                f"latency {_fmt_latency(result.telemetry.latency_ms)} | "
                f"tokens {_fmt_num(result.telemetry.total_tokens)} | "
                f"cost {_fmt_cost(result.telemetry.cost_usd)} | "
                f"trace {_fmt_trace(result.telemetry.trace_status)}"
            )
```

with:

```python
    for result in summary.results:
        if result.telemetry is not None:
            lines.append(
                f"{result.case_id} {result.strategy_name}: "
                f"{'pass' if result.passed else 'fail'} — {result.score_reason} | "
                f"latency {format_latency(result.telemetry.latency_ms, unavailable='unavailable')} | "
                f"tokens {format_number(result.telemetry.total_tokens, unavailable='unavailable')} | "
                f"cost {format_cost(result.telemetry.cost_usd, unavailable='unavailable')} | "
                f"trace {format_trace(result.telemetry.trace_status, unavailable='unavailable')}"
            )
```

- [ ] **Step 3: Run tests to verify green**

Run: `pytest tests/test_evals.py -v`
Expected: PASS, output text identical to before.

- [ ] **Step 4: Commit**

```bash
git add src/openrouter_demo/evals.py
git commit -m "refactor: inline single-use _fmt_* formatting wrappers in evals.py"
```

---

### Task 10: Merge `format_latency` into `format_number`

**Files:**
- Modify: `src/openrouter_demo/formatting.py`

**Interfaces:**
- Consumes: `is_unavailable`, `format_number` (both already defined earlier in the same file).
- Produces: `format_latency(value, *, unavailable)` keeps its exact signature and behavior — `evals.py` and any other caller need no changes. Behavior to preserve: when `value` is unavailable, return `unavailable` verbatim (not `"unavailable ms"`); when available, return `format_number`'s output with `" ms"` appended.

- [ ] **Step 1: Write the failing-if-wrong check first (informal, no new test file needed — this is pure refactor of a pure function)**

Confirm current behavior by running the existing formatting-dependent tests before editing:

Run: `pytest tests/test_evals.py -v`
Expected: PASS (baseline, to diff against after the change).

- [ ] **Step 2: Rewrite `format_latency` in terms of `format_number`**

Replace in `src/openrouter_demo/formatting.py`:

```python
def format_latency(value: float | int | Unavailable | None, *, unavailable: str) -> str:
    if is_unavailable(value):
        return unavailable
    return f"{value:g} ms"
```

with:

```python
def format_latency(value: float | int | Unavailable | None, *, unavailable: str) -> str:
    formatted = format_number(value, unavailable=unavailable)
    return formatted if is_unavailable(value) else f"{formatted} ms"
```

- [ ] **Step 3: Run tests to verify no behavior change**

Run: `pytest tests/test_evals.py -v`
Expected: PASS, identical output to Step 1's baseline.

- [ ] **Step 4: Commit**

```bash
git add src/openrouter_demo/formatting.py
git commit -m "refactor: express format_latency in terms of format_number"
```

---

### Task 11: Inline `_heading()` in `ui.py`

**Files:**
- Modify: `src/openrouter_demo/ui.py`
- Modify: `tests/test_ui.py`

**Interfaces:**
- Consumes: `ui.html` from `nicegui` (already imported).
- Produces: every call site now calls `ui.html(text, tag=f"h{level}").classes(classes)` directly; behavior identical since `_heading` was a pure pass-through.

Current call sites of `_heading(text, level=N, classes=C)` in `src/openrouter_demo/ui.py`:
1. `_heading("Production Inference Lab", level=1, classes="demo-page-title")`
2. `_heading("LLM Response", level=2, classes="demo-response-status")`  — *(actual call inside `response_panel`, verify exact text/classes at the call site before editing — see Step 2)*
3. `_heading("Prompt routing, traceability, and evaluation come together for meaningful production inference", level=3, classes="text-section-heading")`
4. `_heading("Prompt Evaluation Scenario", level=5, classes="text-section-heading")`
5. `_heading("Prompt Evaluation", level=5, classes="text-section-heading")`
6. `_heading("Prompt", level=2, classes="demo-section-heading")`
7. `_heading("Strategy", level=2, classes="demo-component-heading")`
8. `_heading("Evaluation Scores", level=2, classes="demo-section-heading demo-scores-heading")`

- [ ] **Step 1: Delete the function**

Remove:

```python
def _heading(text: str, *, level: int, classes: str) -> None:
    ui.html(text, tag=f"h{level}").classes(classes)


```

- [ ] **Step 2: Replace each call site**

For each of the 8 call sites listed above, replace the pattern:

```python
_heading(TEXT, level=N, classes=CLASSES)
```

with:

```python
ui.html(TEXT, tag="hN").classes(CLASSES)
```

substituting the literal `N` into the tag string (e.g. `tag="h1"`, `tag="h2"`, `tag="h3"`, `tag="h5"`) and keeping `TEXT`/`CLASSES` byte-for-byte identical to the original call.

- [ ] **Step 3: Update the test that greps for a `_heading(...)` call literally**

In `tests/test_ui.py`, in `test_ui_has_no_chatbot_labels`, change:

```python
        '_heading("Production Inference Lab", level=1, classes="demo-page-title")',
```

to:

```python
        'ui.html("Production Inference Lab", tag="h1").classes("demo-page-title")',
```

- [ ] **Step 4: Run tests to verify green**

Run: `pytest tests/test_ui.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/openrouter_demo/ui.py tests/test_ui.py
git commit -m "refactor: inline single-use _heading() wrapper"
```

---

## Self-Review Notes

- **Spec coverage:** 11 of the 12 originally-proposed items are covered (Tasks 1–11). The 12th (`STRATEGY_MODELS`/`STRATEGY_MODEL_SHORT_NAMES`) was dropped after verification — see the Spec section above.
- **Ordering:** Tasks 2, 3, 4 all touch `models.py` but in disjoint regions (enum, dataclass method, dataclasses+fields) and are committed independently, so each is revertable without conflicting with the others. Task 4 and 5 both touch `tests/test_routing.py`'s import line for `openrouter_demo.models`/`openrouter_demo.routing`; Task 4's step explicitly notes the `UNAVAILABLE` import is left for Task 5 to remove, since Task 4 only deletes the tests that used it for `AttemptRecord`/`FallbackEvidence`, and Task 5 deletes the test that used it for `FALLBACK_PRIMARY_STRATEGY`.
- **Type/name consistency:** Verified against current file contents (read in full before writing this plan) — no placeholder text, no invented function names. `_UNAVAILABLE_COPY`/`_COST_UNAVAILABLE_COPY` in Task 7 and `format_cost`/`format_trace` in Task 7/9 are the actual existing names in `ui.py`/`formatting.py`.
