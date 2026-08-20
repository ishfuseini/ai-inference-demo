# Phase 4: Telemetry, Repeat, and Observability - Pattern Map

**Mapped:** 2026-08-19
**Files analyzed:** 13 (6 modified source, 3 new tests, 4 extended/updated tests)
**Analogs found:** 13 / 13

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/openrouter_demo/models.py` | model | transform | `src/openrouter_demo/models.py` (itself) | exact (extend `TelemetryEvidence`, add `RepeatObservation`) |
| `src/openrouter_demo/client.py` | service | streaming | `src/openrouter_demo/client.py` (itself) | exact (add header + cache/router extractors) |
| `src/openrouter_demo/telemetry.py` | service | request-response (side-effect) | `src/openrouter_demo/telemetry.py` (itself) + `config.py` | exact (add conditional trace helper) |
| `src/openrouter_demo/scenarios.py` | service | streaming | `src/openrouter_demo/scenarios.py` (itself) `run_fallback_scenario` | exact (add `run_repeat_scenario`) |
| `src/openrouter_demo/sqlite_store.py` | store | CRUD / file-I/O | `src/openrouter_demo/sqlite_store.py` (itself) | exact (fix round-trip) |
| `src/openrouter_demo/ui.py` | component | event-driven | `src/openrouter_demo/ui.py` (itself) | exact (extend rows/panels/handlers) |
| `tests/test_telemetry.py` | test | request-response | `tests/test_imports.py` + `tests/test_ui.py` | exact (no-network, construct config objects) |
| `tests/test_repeat.py` | test | streaming | `tests/test_scenarios.py` | exact (injected `stream_fn`, `asyncio.run`) |
| `tests/test_sqlite_store.py` | test | CRUD / file-I/O | `src/openrouter_demo/sqlite_store.py` + `tests/test_ui.py` | role-match (tmp_path DB + direct `InferenceRun` construction) |
| `tests/test_client.py` | test | streaming | `tests/test_client.py` (itself) | exact (extend with metadata header + cache asserts) |
| `tests/test_scenarios.py` | test | streaming | `tests/test_scenarios.py` (itself) | exact (extend with repeat scenario) |
| `tests/test_ui.py` | test | event-driven | `tests/test_ui.py` (itself) | exact (extend row/column assertions) |
| `tests/test_phase1_guards.py` | test | static-analysis | `tests/test_phase1_guards.py` (itself) | exact (replace Langfuse forbidden-string guard) |

## Pattern Assignments

### `src/openrouter_demo/models.py` (model, transform)

**Analog:** itself — extend existing types

**Sentinel + enum pattern** (lines 6-24):
```python
@dataclass(frozen=True)
class Unavailable:
    label: str = "unavailable"

    def __bool__(self) -> bool:
        return False


UNAVAILABLE = Unavailable()


class Status(StrEnum):
    PENDING = "pending"
    STREAMING = "streaming"
    SUCCEEDED = "succeeded"
    FALLBACK_SUCCEEDED = "fallback_succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

**TelemetryEvidence — current fields** (lines 43-51):
```python
@dataclass(frozen=True)
class TelemetryEvidence:
    model: str | Unavailable
    provider: str | Unavailable
    latency_ms: int
    prompt_tokens: int | Unavailable
    completion_tokens: int | Unavailable
    total_tokens: int | Unavailable
    cost_usd: float | Unavailable
```

**What to add (all defaulted so existing constructors stay valid):**
```python
    # NEW — defaults keep the ~15 existing construction sites working:
    cache_status: str | Unavailable = UNAVAILABLE      # "hit" | "write" | UNAVAILABLE
    cached_tokens: int | Unavailable = UNAVAILABLE
    cache_write_tokens: int | Unavailable = UNAVAILABLE
    trace_status: str | Unavailable = UNAVAILABLE      # "enabled" | "disabled" | "failed"
    trace_id: str | None = None
    trace_url: str | None = None
```

**What to add — `RepeatObservation`** (mirror `FallbackEvidence` at lines 67-70):
```python
@dataclass(frozen=True)
class RepeatObservation:
    first: StreamedResult
    second: StreamedResult
    cache_status: str | Unavailable
    cached_tokens: int | Unavailable
    cache_write_tokens: int | Unavailable
```

**Constraint:** `InferenceRun` is `frozen=True` and constructed with keyword args in `ui.py` and tests; adding fields to `TelemetryEvidence` (not `InferenceRun`) keeps all `InferenceRun(...)` sites unchanged. Do NOT reorder existing fields.

---

### `src/openrouter_demo/client.py` (service, streaming)

**Analog:** itself — add header + extractors, extend `StreamedResult` fields

**Headers block to extend** (lines 121-124):
```python
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
```
**What to add:** `"X-OpenRouter-Metadata": "enabled"` to this dict. This is the opt-in header for router metadata.

**Extractor pattern to mirror** (`_extract_usage`, lines 78-97) — add a sibling `_extract_cache`:
```python
def _extract_usage(payload: dict) -> tuple[int | Unavailable, int | Unavailable, int | Unavailable, float | Unavailable]:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return UNAVAILABLE, UNAVAILABLE, UNAVAILABLE, UNAVAILABLE
    # ... per-key isinstance() checks, UNAVAILABLE on missing/non-int
    pt: int | Unavailable = prompt_tokens if isinstance(prompt_tokens, int) else UNAVAILABLE
    # ...
    return pt, ct, tt, co
```
**What to add — `_extract_cache(usage: dict) -> tuple[str | Unavailable, int | Unavailable, int | Unavailable]`:** read `usage["prompt_tokens_details"]`; `cached_tokens > 0` → `"hit"`, `cache_write_tokens > 0` → `"write"`, else `UNAVAILABLE` triplet. Do NOT key on `openrouter_metadata` (stripped from cache hits).

**Metadata-capture block** (lines ~175-194) — extend with cache/router state:
```python
                    pt, ct, tt, co = _extract_usage(payload)
                    if not isinstance(pt, Unavailable):
                        seen_pt = pt
                    # ... same guard-then-assign for each field
```
**What to add:** `seen_cache_status`/`seen_cached_tokens`/`seen_cache_write_tokens` initialized to `UNAVAILABLE`, and `seen_router_metadata: dict | Unavailable = UNAVAILABLE` captured from `payload.get("openrouter_metadata")` on the final chunk.

**Final result construction** (lines ~219-231) — extend `StreamedResult`:
```python
        yield StreamedResult(
            text=full_text,
            model=final_model,
            provider=seen_provider,
            prompt_tokens=seen_pt,
            completion_tokens=seen_ct,
            total_tokens=seen_tt,
            cost_usd=seen_cost,
            latency_ms=latency_ms,
        )
```
**What to add:** cache fields + `openrouter_metadata` (defaulted on `StreamedResult` so existing tests constructing it positionally remain valid — mirror the `InferenceRun` non-breaking-default approach).

**Preserve:** error classes (`OpenRouterError`/`OpenRouterAuthError`/`OpenRouterHTTPError`/`OpenRouterTimeoutError`, lines 15-40) are caught by scenarios; the SSE `data:` loop and `owns_client` cleanup must remain intact.

---

### `src/openrouter_demo/telemetry.py` (service, request-response side-effect)

**Analog:** itself + `config.py`

**Current pattern** (lines 6-14):
```python
@dataclass(frozen=True)
class TraceReadiness:
    enabled: bool
    detail: str


def trace_readiness_from_config(config: AppConfig) -> TraceReadiness:
    if config.langfuse_ready:
        return TraceReadiness(enabled=True, detail="Langfuse credentials are configured.")
    return TraceReadiness(enabled=False, detail="Langfuse tracing disabled; optional env vars are incomplete.")
```

**What to add — `TraceOutcome` + `record_trace` (never raises on missing credentials):**
```python
@dataclass(frozen=True)
class TraceOutcome:
    status: str            # "enabled" | "disabled" | "failed"
    trace_id: str | None
    trace_url: str | None

def record_trace(
    config: AppConfig,
    *,
    name: str,
    model: str,
    input: dict,
    output: str,
    usage_details: dict[str, int],
) -> TraceOutcome:
    if not config.langfuse_ready:
        return TraceOutcome(status="disabled", trace_id=None, trace_url=None)
    try:
        from langfuse import get_client  # import inside branch, never at module import time
        client = get_client()
        with client.start_as_current_observation(
            name=name, as_type="generation", model=model,
            input=input, output=output, usage_details=usage_details,
        ) as gen:
            pass
        client.flush()
        return TraceOutcome(
            status="enabled",
            trace_id=gen.trace_id,
            trace_url=client.get_trace_url(trace_id=gen.trace_id),
        )
    except Exception:
        return TraceOutcome(status="failed", trace_id=None, trace_url=None)
```

**Constraint:** keep `trace_readiness_from_config` — `test_imports.py::test_trace_readiness_uses_config_without_creating_traces` and `test_ui.py` depend on it. Construct `get_client()` only inside the `langfuse_ready` branch.

---

### `src/openrouter_demo/scenarios.py` (service, streaming)

**Analog:** itself `run_fallback_scenario` (lines 31-100)

**Result dataclass pattern** (lines 24-28):
```python
@dataclass(frozen=True)
class FallbackResult:
    primary: AttemptRecord
    fallback: StreamedResult | None
    simulated: bool
```

**Two-run async-generator pattern to mirror** (lines 31-37 + the attempt loop):
```python
async def run_fallback_scenario(
    prompt: str,
    *,
    fallback_strategy: RoutingStrategy,
    api_key: str,
    stream_fn: StreamFn = stream_chat_completion,
) -> AsyncIterator[StreamChunk | FallbackResult]:
```

**What to add — `run_repeat_scenario`:** signature `async def run_repeat_scenario(prompt, *, strategy, api_key, stream_fn=stream_chat_completion) -> AsyncIterator[StreamChunk | RepeatObservation]`. Run the same `stream_fn` twice with the same `strategy`, yielding `StreamChunk` events from run 2 for progressive display, collecting each run's `StreamedResult`. Use `time.monotonic()` for latency (same as `client.py`). Compute cache status from run 2's cache fields (OBS-03), else emit a `RepeatObservation` carrying both results and a cache status of `UNAVAILABLE` so the UI renders the observed latency/cost delta (OBS-04). Yield a final `RepeatObservation` with `first`/`second`/`cache_status`/`cached_tokens`/`cache_write_tokens`.

**Preserve:** `PhaseNotImplementedError` (line 20) and `FallbackResult`/`run_fallback_scenario` — `test_imports.py` and `test_scenarios.py` import them.

---

### `src/openrouter_demo/sqlite_store.py` (store, CRUD / file-I/O)

**Analog:** itself — fix `_row_to_run` and add explicit (de)serialization

**Persist side** (`append`, lines 43-52):
```python
    def append(self, run: InferenceRun) -> None:
        telemetry_json = json.dumps(asdict(run.telemetry) if run.telemetry is not None else None)
```
**Problem:** `asdict` turns `UNAVAILABLE` into `{"label": "unavailable"}`; new cache/trace fields are stored but dropped on reload.

**Reload side** (`_row_to_run`, lines 84-103) — the fix target:
```python
    def _row_to_run(self, row: sqlite3.Row) -> InferenceRun:
        telemetry = None
        if row["telemetry_json"]:
            tel = json.loads(row["telemetry_json"])
            if tel is not None:
                telemetry = TelemetryEvidence(
                    model=tel.get("model"),
                    provider=tel.get("provider"),
                    latency_ms=tel.get("latency_ms") or 0,
                    # ... only 7 fields, no sentinel mapping
                )
```
**What to change:**
1. Add `TelemetryEvidence.to_dict()` / `TelemetryEvidence.from_dict()` (or module-level helpers) in `models.py` that map `UNAVAILABLE` ↔ a sentinel string (e.g. `"__unavailable__"`) and round-trip all fields including cache/trace.
2. Call them from `append` (store `to_dict`) and `_row_to_run` (rebuild via `from_dict`), passing all fields.
3. Persist `fallback_evidence` (or its JSON) so comparison survives restart.

**DB schema:** `_init_db` (lines 26-40) creates the `runs` table. If new columns are added instead of extending `telemetry_json`, mirror the `CREATE TABLE IF NOT EXISTS` + `CREATE INDEX` style and keep the `REPLACE INTO` parameter tuple in sync with column order.

---

### `src/openrouter_demo/ui.py` (component, event-driven)

**Analog:** itself — extend rows, history columns, and handlers

**Format helpers to reuse** (lines 41-63) — never stringify `UNAVAILABLE` directly:
```python
def _format_metadata(value: str | Unavailable) -> str: ...
def _format_tokens(value: int | Unavailable) -> str: ...
def _format_latency(value: int | Unavailable) -> str: ...
def _format_cost(value: float | Unavailable) -> str: ...
```

**Telemetry rows pattern** (`_telemetry_rows`, line 89) — append Cache/repeat + Trace rows:
```python
    rows = [
        ("Status", status),
        ("Strategy", strategy),
        ("Model", _format_metadata(telemetry.model) if telemetry else ...),
        # ...
    ]
    if run.fallback_evidence is not None:
        # ... conditional rows
    return rows
```
**What to add:** after the Cost row, append a `("Cache", ...)` row (hit/write/unavailable copy, or repeat delta per OBS-04) and a `("Trace", ...)` row (trace URL when `trace_status == "enabled"`, `TRACE_DISABLED` copy otherwise). The `is_running`/`run is None` branches must add matching `("Cache", ...)`/`("Trace", ...)` placeholder rows so the table shape stays consistent.

**History rows pattern** (`_history_rows`, line 153, 8-tuple) — extend to 10 columns:
```python
def _history_rows(history: RunHistory) -> list[tuple[str, str, str, str, str, str, str, str]]:
    # ... fallback_label = "Yes" if run.fallback_evidence is not None else "—"
```
**What to add:** `cache` and `trace` labels appended to each row tuple (10 total), and update the `columns` tuple in `_render_history` (line 190) to `("Run", "Strategy", "Model", "Provider", "Latency", "Tokens", "Cost", "Fallback", "Cache", "Trace")`. `test_ui.py::test_history_rows_include_fallback_column` asserts `len(rows[0]) == 8` — update to 10 in the same wave.

**Run handler pattern** (`run_request` inside `build_app`, ~line 390) — add Repeat branch:
```python
        selected_strategy = STRATEGIES.get(strategy_select.value, DEFAULT_STRATEGY)
        if simulate_failure.value:
            run = await _run_fallback_inference(...)
        else:
            run = await _run_inference(...)
```
**What to add:** a `repeat_enabled` switch (mirror the `simulate_failure = ui.switch(...)` control, ~line 455) and an `elif repeat_enabled.value:` branch calling a new `_run_repeat_inference` helper. That helper mirrors `_run_fallback_inference` (line 281): consume `run_repeat_scenario` events, build `InferenceRun` with `telemetry` from the second run, append to `history`, and set a repeat status copy.

**Remove:** the "Future operation panels" card (end of `build_app`) that reserves Cache/trace/eval for later phases — its `LANGFUSE_ENV_VARS` copy is superseded by real trace rendering.

---

### `tests/test_telemetry.py` (test, request-response) — NEW FILE

**Analog:** `tests/test_imports.py` (config-object construction, no network) + `tests/test_ui.py` (direct model construction)

**Pattern to follow** (`test_imports.py::test_trace_readiness_uses_config_without_creating_traces`, lines 71-86):
```python
def test_trace_readiness_uses_config_without_creating_traces() -> None:
    disabled = trace_readiness_from_config(load_config({}))
    enabled = trace_readiness_from_config(
        load_config(
            {
                LANGFUSE_PUBLIC_KEY: "pk",
                LANGFUSE_SECRET_KEY: "sk",
                LANGFUSE_BASE_URL: "https://cloud.langfuse.com",
            }
        )
    )
    assert disabled.enabled is False
    assert enabled.enabled is True
```

**What to test:**
1. `record_trace(config=load_config({}), ...)` returns `TraceOutcome(status="disabled", trace_id=None, trace_url=None)` — and constructs no Langfuse client.
2. `record_trace` with a config whose `langfuse_ready=True` but bad env/endpoint returns `status="failed"` (never raises).
3. `TelemetryEvidence.from_dict(TelemetryEvidence.to_dict(...))` round-trips `UNAVAILABLE` sentinels and cache/trace fields (`cached_tokens is UNAVAILABLE`, not `{"label": "unavailable"}`).

---

### `tests/test_repeat.py` (test, streaming) — NEW FILE

**Analog:** `tests/test_scenarios.py` (injected `stream_fn` dual-stream, `asyncio.run`)

**Pattern to follow** (`test_scenarios.py:8-47`):
```python
def _dual_stream() -> object:
    call_count = 0

    async def stream(*_args: object, **_kwargs: object) -> AsyncIterator[StreamChunk | StreamedResult]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OpenRouterHTTPError("...", status_code=404, partial_text="")
        yield StreamChunk("Fallback ")
        yield StreamChunk("response")
        yield StreamedResult(...)
    return stream


def _collect_events(stream: object) -> list[object]:
    async def _run() -> list[object]:
        events: list[object] = []
        async for event in run_fallback_scenario("test prompt", fallback_strategy=DEFAULT_STRATEGY, api_key="sk-test", stream_fn=stream):
            events.append(event)
        return events
    return asyncio.run(_run())
```

**What to test:** a two-call fake stream where call 2 returns `prompt_tokens_details` with `cached_tokens > 0` → `RepeatObservation.cache_status == "hit"`; and a second fake stream with no `prompt_tokens_details` → `cache_status is UNAVAILABLE` while `first`/`second` latency/cost are populated (OBS-03/OBS-04 honesty assertions). Assert both `StreamChunk` progressive yields and the final `RepeatObservation`.

---

### `tests/test_sqlite_store.py` (test, CRUD / file-I/O) — NEW FILE

**Analog:** `src/openrouter_demo/sqlite_store.py` API + `tests/test_ui.py` direct `InferenceRun`/`TelemetryEvidence` construction

**DB fixture pattern to use** (pytest `tmp_path`):
```python
def test_round_trip_preserves_sentinels(tmp_path) -> None:
    store = SQLiteRunHistory(db_path=str(tmp_path / "runs.db"))
    run = InferenceRun(..., telemetry=TelemetryEvidence(model=UNAVAILABLE, ..., cache_status="hit", cached_tokens=10, trace_status="disabled"))
    store.append(run)
    reloaded = store.get(run.run_id)
    assert reloaded.telemetry.model is UNAVAILABLE
    assert reloaded.telemetry.cached_tokens == 10
```

**Construction pattern to copy** (`tests/test_ui.py::test_telemetry_and_history_rows_render_unavailable_copy`, lines 106-138): build `TelemetryEvidence` with `UNAVAILABLE` sentinels and a real `InferenceRun` with `datetime.now(UTC)`.

---

### `tests/test_client.py` (test, streaming) — EXTEND

**Analog:** itself — add cache/metadata assertions to the existing MockTransport harness

**Harness pattern** (lines 12-31) — reuse unchanged:
```python
def _sse_bytes(chunks: list[dict]) -> bytes:
    lines: list[str] = []
    for c in chunks:
        lines.append(f"data: {json.dumps(c)}")
        lines.append("")
    lines.append("data: [DONE]")
    lines.append("")
    return "\n".join(lines).encode()


def _client_with(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))
```

**What to add:**
1. Assert `request.headers.get("x-openrouter-metadata") == "enabled"` in a handler (mirror the existing `authorization` assert at line 44).
2. A chunk with `usage.prompt_tokens_details.cached_tokens > 0` → `result.cached_tokens == N`, `result.cache_status == "hit"`.
3. A stream with no `prompt_tokens_details` → `result.cache_status is UNAVAILABLE` and `result.cached_tokens is UNAVAILABLE` (mirror `test_stream_missing_usage_is_unavailable`, lines 128-150).

---

### `tests/test_scenarios.py` (test, streaming) — EXTEND

**Analog:** itself — add repeat-scenario tests using the same injected `stream_fn` pattern

**What to add:** `_repeat_stream()` (two calls both succeed, second returns cache details) and `_repeat_stream_no_cache()` (second returns no `prompt_tokens_details`). Assert the final `RepeatObservation` fields, mirroring `test_fallback_scenario_primary_fails_fallback_succeeds` (lines 44-59) and `test_fallback_scenario_yields_stream_chunks_progressively` (lines 62-67).

---

### `tests/test_ui.py` (test, event-driven) — EXTEND

**Analog:** itself — extend row/column assertions and add `_run_repeat_inference` coverage

**Run helper pattern** (lines 25-26):
```python
def _run(coro):
    return asyncio.run(coro)
```

**What to add/update:**
1. Update `test_history_rows_include_fallback_column` (line 239) — `len(rows[0]) == 8` becomes `== 10`; assert the new Cache/Trace cells.
2. Add cache/trace rows to `test_telemetry_and_history_rows_render_unavailable_copy` expectations (lines 106-138).
3. Add a `test_run_repeat_inference_*` test mirroring `test_run_fallback_inference_produces_fallback_succeeded_run` (line 350): a two-call fake stream, assert the resulting `InferenceRun.telemetry.cache_status` and that history got the run.

---

### `tests/test_phase1_guards.py` (test, static-analysis) — UPDATE

**Analog:** itself — replace the obsolete Langfuse forbidden-string guard

**Current guard to replace** (lines 24-27):
```python
def test_phase1_does_not_create_langfuse_traces() -> None:
    text = implementation_text()
    for forbidden in ("get_client(", ".trace(", ".start_span(", ".generation("):
        assert forbidden not in text
```

**What to change:** Phase 4 legitimately introduces `get_client(`. Replace with a guard asserting tracing is *conditional* — e.g. assert `get_client(` appears in `telemetry.py` (not in the core inference modules), or assert `langfuse_ready` gating text is present. Keep the other two guards (`fastapi`, database imports) unchanged, and keep the `sqlite_store.py` exclusion in `implementation_text()` (lines 8-12) so the database guard still passes.

---

## Shared Patterns

### Unavailable Sentinels (metadata honesty)
**Source:** `src/openrouter_demo/models.py:6-14`
**Apply to:** `models.py`, `client.py`, `scenarios.py`, `sqlite_store.py`, `ui.py`, all tests
```python
UNAVAILABLE = Unavailable()   # bool(UNAVAILABLE) is False; UNAVAILABLE != 0
```
Rule: never coerce `UNAVAILABLE` to 0/empty; `sqlite_store` must map it explicitly on save/load, and `ui.py` is the only tier that formats it into copy.

### Cache presence keyed on `prompt_tokens_details`, never router metadata
**Source:** `src/openrouter_demo/client.py` `_extract_usage` style + RESEARCH Pattern 3
**Apply to:** `client.py`, `scenarios.py`
`cached_tokens > 0` ⇒ "hit"; `cache_write_tokens > 0` ⇒ "write"; otherwise `UNAVAILABLE`. `openrouter_metadata` is stripped from cache-hit responses — absence is not evidence.

### Conditional Langfuse — tracing must never block inference
**Source:** `src/openrouter_demo/telemetry.py` (new `record_trace`) + `config.py:15-19` (`langfuse_ready`)
**Apply to:** `telemetry.py`, `ui.py`, `scenarios.py`
Construct `get_client()` only inside a `config.langfuse_ready` branch; wrap in try/except → `trace_status="failed"`. Never raise out of a live run.

### Non-breaking frozen dataclass extension
**Source:** `src/openrouter_demo/models.py` (`InferenceRun.fallback_evidence = None` default, line 85)
**Apply to:** `TelemetryEvidence`, `StreamedResult`
Add new fields with defaults at the END; never reorder or add required fields. This is how Phase 3 extended `InferenceRun` without breaking positional construction in `test_ui.py`.

### Test isolation — no network
**Source:** `tests/test_client.py:31-32` (`httpx.MockTransport`), `tests/test_scenarios.py:8-47` (injected `stream_fn`), `tests/test_ui.py` (fake async generators)
**Apply to:** all new/extended tests
All tests inject `stream_fn` or `http_client`; none hit OpenRouter or Langfuse. `test_sqlite_store.py` uses `pytest tmp_path`.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | — | — | Every Phase 4 file has a direct in-repo analog; RESEARCH.md supplies the Langfuse v4 API shape for the one genuinely new external call (`get_client()` / `start_as_current_observation`). |

## Metadata

**Analog search scope:** `src/openrouter_demo/*.py`, `tests/*.py`
**Files scanned:** 13 (6 source modules, 7 test files)
**Pattern extraction date:** 2026-08-19
