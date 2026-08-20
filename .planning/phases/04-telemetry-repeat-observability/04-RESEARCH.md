---
phase: 04-telemetry-repeat-observability
status: complete
sources:
  - .planning/STATE.md
  - .planning/ROADMAP.md
  - .planning/REQUIREMENTS.md
  - .planning/PROJECT.md
  - .planning/config.json
  - .planning/telemetry-schema.md
  - .planning/phases/03-routing-and-fallback-demo/03-RESEARCH.md
  - docs/specs/data-model.md
  - docs/specs/research.md
  - docs/ux/screen-spec.md
  - docs/ux/demo-narrative.md
  - src/openrouter_demo/models.py
  - src/openrouter_demo/client.py
  - src/openrouter_demo/routing.py
  - src/openrouter_demo/scenarios.py
  - src/openrouter_demo/telemetry.py
  - src/openrouter_demo/telemetry_schema.py
  - src/openrouter_demo/history.py
  - src/openrouter_demo/sqlite_store.py
  - src/openrouter_demo/config.py
  - src/openrouter_demo/ui.py
  - src/openrouter_demo/evals.py
  - app.py
  - pyproject.toml
  - tests/test_client.py
  - tests/test_ui.py
  - tests/test_scenarios.py
  - tests/test_routing.py
  - tests/test_imports.py
  - tests/test_config.py
  - tests/test_phase1_guards.py
  - OpenRouter Router Metadata docs (https://openrouter.ai/docs/guides/features/router-metadata)
  - OpenRouter Prompt Caching docs (https://openrouter.ai/docs/features/prompt-caching)
  - Langfuse Python SDK v4 (Context7 `/langfuse/langfuse-python` + installed 4.14.4 package source)
created: 2026-08-19
---

# Phase 04 Research: Telemetry, Repeat, and Observability

## Summary

Phase 4 closes the observability loop over the Phase 2/3 streaming + routing console: every run gets a single normalized telemetry record carrying model/provider, latency, tokens, cost, fallback, cache/repeat, and trace-state fields (OBS-01); the app opts into OpenRouter router metadata and handles its absence explicitly (OBS-02); a repeat/cache scenario reports provider cache metadata only when the provider actually returns it and otherwise falls back to observed repeat latency/cost (OBS-03/OBS-04); Langfuse traces are created only when credentials are configured, with tracing visibly marked disabled otherwise (OBS-05/OBS-06); and recent-run history supports comparison from the main UI (OBS-07).

Two external APIs drive the new behavior. OpenRouter router metadata is **opt-in via the `X-OpenRouter-Metadata: enabled` request header** (default is disabled), and surfaces a top-level `openrouter_metadata` object on the **final streamed chunk before `data: [DONE]`** with `requested`, `strategy`, `region`, `summary`, `attempt`, `is_byok`, `endpoints` (with per-candidate `provider`/`model`/`selected`), `attempts[]` (per-attempt `provider`/`model`/`status`), and `pipeline[]`. Critically, **cache-hit responses never include `openrouter_metadata`** — so cache detection must key on `usage.prompt_tokens_details`, not router metadata. Current cache fields are `usage.prompt_tokens_details.cached_tokens` (tokens read from cache = hit) and `usage.prompt_tokens_details.cache_write_tokens` (tokens written). [VERIFIED: openrouter.ai/docs/guides/features/router-metadata + openrouter.ai/docs/features/prompt-caching]

Langfuse Python SDK v4 (installed `4.14.4`, matching `pyproject.toml` `langfuse>=4.14.4`) replaced the old `trace()`/`generation()`/`span()` methods with a unified `start_observation()` / `start_as_current_observation(as_type=...)` API. `get_client()` reads `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`/`LANGFUSE_BASE_URL`; called without credentials it prints a warning and returns a *disabled* client rather than raising. The returned observation wrapper exposes `.trace_id` and `.id`, and `client.get_trace_url(trace_id=...)` builds `{base_url}/project/{project_id}/traces/{trace_id}`. [VERIFIED: installed langfuse 4.14.4 package source]

**Primary recommendation:** Extend `models.TelemetryEvidence` with cache + trace fields (using defaults so existing constructors don't break), add the `X-OpenRouter-Metadata: enabled` header and cache/`openrouter_metadata` extraction to `client.py`, add a `run_repeat_scenario` to `scenarios.py` and a conditional Langfuse trace helper to `telemetry.py`, and wire cache/trace rows plus a comparison grid and "Repeat" action into `ui.py`. Fix the `SQLiteRunHistory` round-trip so `Unavailable` sentinels and the new fields survive save/load, and **update the Phase 1 Langfuse guard test** (`tests/test_phase1_guards.py:24-27`) which currently forbids the exact strings Phase 4 must introduce.

**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OBS-01 | App records normalized telemetry for every run, including model/provider, latency, tokens, cost, fallback, cache/repeat, and trace state fields. | `TelemetryEvidence` (models.py:43-51) already carries model/provider/latency/tokens/cost. Extend with `cache_status`, `cached_tokens`, `cache_write_tokens`, `trace_status`, `trace_id`, `trace_url` (defaults `= UNAVAILABLE` / `= None`). `data-model.md` already names `cache_status`, `repeat_observation`, `fallback_used`, `trace_status`, `trace_url`. `fallback_used` derives from `InferenceRun.fallback_evidence is not None`. |
| OBS-02 | App opts into OpenRouter router metadata where useful and handles its absence. | Send `X-OpenRouter-Metadata: enabled` header in `client.py:121-124`. Extract `openrouter_metadata` from the final chunk (top-level, sibling of `usage`). Cache-hit responses and some error classes omit it — treat absence as `UNAVAILABLE`, never fabricate. [VERIFIED: router-metadata docs — "Cache Hits: Cache hits never include `openrouter_metadata`"] |
| OBS-03 | Repeat/cache scenario reports provider cache metadata only when available. | Detect presence via `usage.prompt_tokens_details.cached_tokens > 0` (hit) or `cache_write_tokens > 0` (write). Report cache row only when this object exists and is non-zero; otherwise show unavailable copy. [VERIFIED: prompt-caching docs — `cached_tokens`/`cache_write_tokens`] |
| OBS-04 | Repeat/cache scenario reports observed repeat latency and cost when cache metadata unavailable. | When `prompt_tokens_details` absent/zero, compute a `repeat_observation` comparing run-1 vs run-2 latency and cost, and render that comparison instead of cache claims. |
| OBS-05 | App creates Langfuse traces for demo calls when Langfuse credentials are configured. | Gate on `AppConfig.langfuse_ready` (config.py:17). When true, `get_client()` + `start_as_current_observation(as_type="generation", name=..., model=..., input=..., usage_details=...)`, update with output, then `flush()`. Store `.trace_id` + `get_trace_url(trace_id=...)`. [VERIFIED: installed langfuse 4.14.4] |
| OBS-06 | App visibly marks tracing disabled when Langfuse credentials are absent. | `TRACE_DISABLED` copy already exists (ui.py:78). When `langfuse_ready` is false, return `trace_status="disabled"` with no client construction; render the trace row as disabled and keep the existing Langfuse status card (ui.py:486-491). |
| OBS-07 | Recent run history allows comparison of completed runs in the main UI. | `app.py:16-18` wires `SQLiteRunHistory(db_path="data/runs.db")` as the active history store. Extend `_history_rows` (ui.py:153) with Cache and Trace columns and add a comparison section. Fix `sqlite_store._row_to_run` so persisted runs round-trip new fields + `Unavailable` sentinels. |
</phase_requirements>

## Project Constraints (from STATE.md decisions — no Phase 4 CONTEXT.md exists)

These locked decisions from prior phases constrain Phase 4 and MUST NOT be reversed:

- Use direct OpenRouter Chat Completions requests over HTTPS — the demo must not hide OpenRouter-specific routing or metadata behind another router. [VERIFIED: .planning/STATE.md "Keep OpenRouter integration direct and inspectable."]
- Keep Langfuse optional at runtime — missing Langfuse credentials must disable tracing visibly without blocking inference. [VERIFIED: .planning/STATE.md "Keep Langfuse optional."]
- Use `uv`, Ruff, and pytest as the quality-gate path. [VERIFIED: .planning/STATE.md]
- Metadata honesty: token, cost, provider, router, and cache fields must distinguish unavailable from zero values; never claim cache hits that the provider did not report. [VERIFIED: REQUIREMENTS.md Out of Scope "Guaranteed cache hit claims — Cache behavior depends on provider/route metadata and must be reported honestly."]
- Fallback evidence (two-attempt client-side orchestration) from Phase 3 must remain intact; Phase 4 extends telemetry, it does not rework fallback.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Normalized telemetry modeling (`TelemetryEvidence` + cache/trace fields) | API / Backend (`models.py`) | — | Typed frozen dataclass is the single source of truth for every run's normalized record. |
| Router-metadata opt-in + extraction | API / Backend (`client.py`) | — | Owns the HTTPS request; the `X-OpenRouter-Metadata` header and `openrouter_metadata`/cache parsing belong beside existing `_extract_*` helpers. |
| Cache presence detection | API / Backend (`client.py` or `telemetry.py`) | — | Pure function over the parsed usage payload; must be testable without network. |
| Repeat/cache scenario orchestration | API / Backend (`scenarios.py`) | — | Two-run sequence producing a `RepeatObservation`; mirrors the existing `run_fallback_scenario` injection pattern. |
| Langfuse trace creation (conditional) | API / Backend (`telemetry.py`) | — | Owns the optional client; returns a `TraceOutcome` (enabled/disabled/failed + id + url) that never raises on missing credentials. |
| Run persistence + comparison source | Database / Storage (`sqlite_store.py`) | Browser / Client (`ui.py`) | `app.py` already uses `SQLiteRunHistory`; persistence must round-trip new fields and sentinels for OBS-07 comparison. |
| Cache/trace/repeat rendering + comparison UI | Browser / Client (`ui.py`) | — | Extends `_telemetry_rows`/`_history_rows` and the NiceGUI panels; rendering is the only tier allowed to format `Unavailable` into copy. |
| Eval scoring | API / Backend (`evals.py`) | — | Out of scope for Phase 4 (Phase 5). Leave the `PhaseNotImplementedError` stub alone. |

## Standard Stack

### Core

No new packages. Phase 4 uses the existing Phase 1-3 stack plus the already-installed `langfuse` dependency.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python 3.12+ | ≥3.12 (venv is 3.13) | Application runtime | Project constraint [VERIFIED: pyproject.toml:5 `requires-python = ">=3.12"`] |
| NiceGUI | ≥3.16.0 | Local browser UI | Project constraint [VERIFIED: pyproject.toml:8 `"nicegui>=3.16.0"`] |
| httpx | ≥0.28.1 | Async HTTP for OpenRouter | Project constraint [VERIFIED: pyproject.toml:9 `"httpx>=0.28.1"`] |
| langfuse | ≥4.14.4 (installed 4.14.4) | Optional trace/observability | Project constraint [VERIFIED: pyproject.toml:11 `"langfuse>=4.14.4"`; installed 4.14.4 confirmed via `uv run python -c "import langfuse; print(langfuse.__version__)"`] |
| pytest | ≥9.1.1 | Focused tests | Project constraint [VERIFIED: pyproject.toml:14 `"pytest>=9.1.1"`] |
| Ruff | ≥0.16.3 | Linting and formatting | Project constraint [VERIFIED: pyproject.toml:15 `"ruff>=0.16.3"`] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx.MockTransport | (built into httpx) | No-network test transport | All client/scenario tests — already used in `tests/test_client.py` (`_client_with`) |
| `langfuse.get_client()` | 4.14.4 | Conditional trace client | Only inside a `config.langfuse_ready` branch; never at module import time |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct `X-OpenRouter-Metadata` header | OpenRouter SDK / client library | SDK would hide the header and metadata behind another layer; direct HTTPS keeps the demo inspectable. [VERIFIED: docs/specs/research.md — "Direct requests keep the demo focused on OpenRouter behavior instead of hiding it behind another router or SDK."] |
| Langfuse v4 unified `start_as_current_observation` | Old `trace()`/`generation()`/`span()` methods | Those methods are removed in v4; the unified API with `as_type` is the only supported path. [VERIFIED: installed 4.14.4 — old methods absent] |
| `cost_details` via Langfuse | Storing cost in `metadata` | `cost_details` is the intended cost channel, but its accepted key format is ambiguous (see Pitfall 7) — keep cost in `metadata` if unsure. |
| In-memory `RunHistory` | SQLite `SQLiteRunHistory` | `app.py` already wires SQLite; keeping it gives OBS-07 persistence across restarts. `RunHistory` remains the test-only store. |

**Installation:**

```bash
# No new packages to install. langfuse 4.14.4 is already in the lockfile/environment.
uv sync
```

**Version verification:** `langfuse` 4.14.4 verified installed and importable. The v4 unified observation API (`start_observation`, `start_as_current_observation`, `get_trace_url`, `flush`) is present on the client; the removed `get_trace_context` and old `trace()`/`generation()` methods are absent. [VERIFIED: installed package introspection]

## Package Legitimacy Audit

No new packages introduced in this phase. `langfuse` is already a declared dependency (Phase 1) and is installed at 4.14.4 from the official `langfuse/langfuse-python` project.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| langfuse | PyPI | existing | existing | github.com/langfuse/langfuse-python | OK | Approved (Phase 1, re-verified 4.14.4 installed) |
| nicegui | PyPI | existing | existing | github.com/zauberzeug/nicegui | OK | Approved (Phase 1) |
| httpx | PyPI | existing | existing | github.com/encode/httpx | OK | Approved (Phase 1) |
| pytest | PyPI | existing | existing | github.com/pytest-dev/pytest | OK | Approved (Phase 1) |
| ruff | PyPI | existing | existing | github.com/astral-sh/ruff | OK | Approved (Phase 1) |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```text
User enters prompt, selects strategy, toggles Repeat/Cache or failure sim
        │
        ▼
┌──────────────────────────────────────────────────┐
│ ui.py run_request()                              │
│  reads strategy + toggles; calls _run_* helpers  │
└──────────┬───────────────────────────────────────┘
           │
     normal / repeat / fallback path
           │
           ▼
┌──────────────────────────────────────────────────┐
│ client.py stream_chat_completion()               │
│  headers: Authorization + X-OpenRouter-Metadata: │
│           enabled                                │
│  per SSE chunk: extract model/provider/usage     │
│  + openrouter_metadata + prompt_tokens_details   │
│  final chunk -> StreamedResult(+ cache + router) │
└──────────┬───────────────────────────────────────┘
           │ StreamedResult / FallbackResult / RepeatResult
           ▼
┌──────────────────────────────────────────────────┐
│ telemetry.py normalize + optional trace          │
│  TelemetryEvidence(cache_status, cached_tokens,  │
│    cache_write_tokens, trace_status, trace_id,   │
│    trace_url)                                    │
│  if config.langfuse_ready:                       │
│    get_client() -> start_as_current_observation  │
│      (as_type="generation", usage_details=...)   │
│    trace_id + get_trace_url(trace_id=...)        │
│  else: trace_status="disabled", no client        │
└──────────┬───────────────────────────────────────┘
           │ InferenceRun (with telemetry + fallback_evidence)
           ▼
┌──────────────────────────────────────────────────┐
│ sqlite_store.SQLiteRunHistory.append()           │
│  persists telemetry_json (asdict) + run fields   │
└──────────┬───────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────┐
│ ui.py render                                     │
│  Telemetry panel: + Cache/repeat row, Trace row  │
│  History: + Cache, Trace columns                 │
│  Comparison: sortable recent-run grid (OBS-07)   │
└──────────────────────────────────────────────────┘
```

### Recommended Project Structure

```text
src/openrouter_demo/
├── models.py        # EXTEND TelemetryEvidence: cache_status, cached_tokens,
│                    #   cache_write_tokens, trace_status, trace_id, trace_url (defaults);
│                    #   ADD RepeatObservation dataclass
├── client.py        # ADD X-OpenRouter-Metadata header; extract openrouter_metadata
│                    #   + prompt_tokens_details.{cached_tokens,cache_write_tokens};
│                    #   extend StreamedResult with cache/router fields
├── telemetry.py     # ADD conditional Langfuse trace helper + TraceOutcome;
│                    #   keep trace_readiness_from_config
├── scenarios.py     # ADD run_repeat_scenario() — two-run repeat/cache observation
├── sqlite_store.py  # FIX round-trip: preserve Unavailable sentinels + new fields;
│                    #   ADD cache/trace columns (or extend telemetry_json)
├── ui.py            # ADD Cache/repeat + Trace telemetry rows, history columns,
│                    #   comparison panel, Repeat action; remove "Future operation panels"
├── routing.py       # No changes (Phase 3 complete)
├── history.py       # No changes (test-only in-memory store)
├── config.py        # No changes (langfuse_ready already present)
└── evals.py         # No changes (Phase 5 scope)
tests/
├── test_telemetry.py      # NEW: normalization + Langfuse toggle behavior
├── test_repeat.py         # NEW: repeat/cache scenario cache-honesty assertions
├── test_client.py         # EXTEND: metadata header sent; cache/absent extraction
├── test_sqlite_store.py   # NEW: round-trip preserves sentinels + new fields
├── test_ui.py             # EXTEND: cache/trace rows, comparison columns, Repeat action
├── test_scenarios.py      # EXTEND: repeat scenario (cache present vs absent)
├── test_phase1_guards.py  # UPDATE: Langfuse guard no longer forbids get_client(/.trace(
├── test_routing.py        # No changes
├── test_imports.py        # EXTEND: new types importable; no cases.json regression
└── test_config.py         # No changes
```

### Pattern 1: Extend `TelemetryEvidence` with Defaults (Non-Breaking)

**What:** Add cache and trace fields to the frozen `TelemetryEvidence` dataclass using default sentinel values so every existing constructor site (`ui.py::_run_inference`, `ui.py::_run_fallback_inference`, `sqlite_store._row_to_run`, and all tests) keeps working unchanged.

**When to use:** Always for this phase — do NOT add required (no-default) fields; that would break ~15 construction sites.

**Example:**
```python
# Source: [VERIFIED: src/openrouter_demo/models.py:43-51 — existing fields]
# Extend non-breakingly:

@dataclass(frozen=True)
class TelemetryEvidence:
    model: str | Unavailable
    provider: str | Unavailable
    latency_ms: int
    prompt_tokens: int | Unavailable
    completion_tokens: int | Unavailable
    total_tokens: int | Unavailable
    cost_usd: float | Unavailable
    # NEW — all defaulted so existing constructors remain valid:
    cache_status: str | Unavailable = UNAVAILABLE      # "hit" | "write" | UNAVAILABLE
    cached_tokens: int | Unavailable = UNAVAILABLE
    cache_write_tokens: int | Unavailable = UNAVAILABLE
    trace_status: str | Unavailable = UNAVAILABLE      # "enabled" | "disabled" | "failed"
    trace_id: str | None = None
    trace_url: str | None = None
```

### Pattern 2: Conditional Langfuse Tracing That Never Raises

**What:** A helper returns a `TraceOutcome` (status + optional id/url). It constructs the Langfuse client **only** when `config.langfuse_ready` is true, and wraps the trace in a try/except so a tracing failure is recorded as `trace_status="failed"` rather than failing the inference run.

**When to use:** Every live run and the repeat scenario. The rule is: tracing is a side-effect that must never block or break inference (project constraint "Langfuse optional at runtime").

**Example:**
```python
# Source: [VERIFIED: installed langfuse 4.14.4 API — get_client, start_as_current_observation,
#          LangfuseObservationWrapper.trace_id, Langfuse.get_trace_url]

from dataclasses import dataclass
from langfuse import get_client

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
        client = get_client()  # reads LANGFUSE_* env vars
        with client.start_as_current_observation(
            name=name,
            as_type="generation",
            model=model,
            input=input,
            output=output,
            usage_details=usage_details,
        ) as gen:
            pass  # context manager auto-ends the observation on exit
        client.flush()
        trace_id = gen.trace_id          # set on the wrapper in __init__
        return TraceOutcome(
            status="enabled",
            trace_id=trace_id,
            trace_url=client.get_trace_url(trace_id=trace_id),
        )
    except Exception:
        return TraceOutcome(status="failed", trace_id=None, trace_url=None)
```

### Pattern 3: Cache-Presence Detection Keyed on `prompt_tokens_details`

**What:** A pure predicate decides whether cache metadata is "present" (report it) or "absent" (fall back to observed latency/cost). It must NOT key on `openrouter_metadata`, which is stripped from cache-hit responses.

**When to use:** In `client.py` extraction and in the repeat scenario's OBS-03/OBS-04 branch.

**Example:**
```python
# Source: [VERIFIED: openrouter.ai/docs/features/prompt-caching — usage object example]
# {
#   "usage": {
#     "prompt_tokens": 10339,
#     "completion_tokens": 60,
#     "total_tokens": 10399,
#     "prompt_tokens_details": { "cached_tokens": 10318, "cache_write_tokens": 0 }
#   }
# }

def _extract_cache(usage: dict) -> tuple[str | Unavailable, int | Unavailable, int | Unavailable]:
    details = usage.get("prompt_tokens_details")
    if not isinstance(details, dict):
        return UNAVAILABLE, UNAVAILABLE, UNAVAILABLE
    cached = details.get("cached_tokens")
    written = details.get("cache_write_tokens")
    ct = cached if isinstance(cached, int) else UNAVAILABLE
    wt = written if isinstance(written, int) else UNAVAILABLE
    if isinstance(ct, int) and ct > 0:
        return "hit", ct, wt
    if isinstance(wt, int) and wt > 0:
        return "write", ct, wt
    return UNAVAILABLE, UNAVAILABLE, UNAVAILABLE  # present object but no cache activity
```

### Anti-Patterns to Avoid

- **Claiming a cache hit from latency/cost alone:** A faster second run does not prove a cache hit. Only `usage.prompt_tokens_details.cached_tokens > 0` proves it. Never infer hit from observed latency. [VERIFIED: REQUIREMENTS.md — "Cache behavior depends on provider/route metadata and must be reported honestly."]
- **Using `openrouter_metadata` to detect cache:** Cache-hit responses strip `openrouter_metadata` entirely; absence of router metadata is not evidence of a cache hit. [VERIFIED: router-metadata docs — "Cache hits never include `openrouter_metadata`"]
- **Calling `get_client()` at import time or unconditionally:** Import-time construction would fail the "no tracing without credentials" constraint and break the test suite. Construct only inside `config.langfuse_ready` branches.
- **Coercing `Unavailable` to zero or empty in persistence:** `dataclasses.asdict` converts the `Unavailable` sentinel into `{"label": "unavailable"}`; naively re-reading that dict as a value breaks metadata honesty on reload. Add explicit `to_dict`/`from_dict` mapping. [VERIFIED: src/openrouter_demo/models.py:6-14 — `Unavailable` is a dataclass with `__bool__` returning False]
- **Leaving two competing telemetry schemas:** `telemetry_schema.py` (`RunRecord`, `FallbackAttempt`) is dead code, unused anywhere in `src/` or `tests/`. The live schema is `models.TelemetryEvidence`. Reconcile or remove it so the repo has one source of truth.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Router metadata extraction | A custom routing-decision parser | OpenRouter `X-OpenRouter-Metadata: enabled` header + `openrouter_metadata` object | OpenRouter already emits `strategy`, `attempts[]`, `endpoints[]`; parsing is a thin, additive decode. [VERIFIED: router-metadata docs] |
| Cache presence detection | Heuristics on latency/cost | `usage.prompt_tokens_details.{cached_tokens,cache_write_tokens}` | The only honest signal; present only when the provider actually reports it. [VERIFIED: prompt-caching docs] |
| Trace transport + flush + URL | Custom OTel exporter or URL string-munging | Langfuse SDK `get_client()` + `start_as_current_observation` + `get_trace_url()` | The SDK handles batching, retries, and the `/project/{id}/traces/{trace_id}` URL. [VERIFIED: installed 4.14.4] |
| SSRF/streaming parsing | A new HTTP layer | Existing `stream_chat_completion` in `client.py` | Already handles SSE `data:` lines, error payloads, timeouts, metadata capture. Only additive extraction is needed. [VERIFIED: src/openrouter_demo/client.py:99-160] |
| Metadata formatting | Ad-hoc string conversion | Existing `_format_metadata`/`_format_tokens`/`_format_cost`/`_format_latency` helpers | Tested and consistent; cache/trace rows reuse them. [VERIFIED: src/openrouter_demo/ui.py:41-61] |

**Key insight:** Phase 4 is additive normalization + one optional side-effect (Langfuse) + one new scenario (repeat/cache). The existing client, models, history, and formatting helpers are sufficient infrastructure; the main work is field extension, one header, one predicate, one scenario function, and persistence round-trip correctness.

## Common Pitfalls

### Pitfall 1: Phase 1 Langfuse Guard Test Fails on First Commit

**What goes wrong:** `tests/test_phase1_guards.py::test_phase1_does_not_create_langfuse_traces` asserts none of `("get_client(", ".trace(", ".start_span(", ".generation(")` appear in the source. Any Langfuse integration introduces `get_client(`.
**Why it happens:** The guard was written for Phase 1 when tracing did not exist; Phase 4 is exactly the phase that introduces it.
**How to avoid:** Update the guard in the same wave as the Langfuse change. Replace the forbidden-string assertion with a guard that tracing is *conditional* — e.g., assert `get_client(` appears only inside a `langfuse_ready` branch, or simply drop the now-obsolete test with a comment.
**Warning signs:** CI red on the first Langfuse commit with no obvious logic error.
**Source:** [VERIFIED: tests/test_phase1_guards.py:24-27 — `for forbidden in ("get_client(", ".trace(", ".start_span(", ".generation("):`]

### Pitfall 2: Cache Claims From a Missing `prompt_tokens_details`

**What goes wrong:** The repeat scenario shows "cache hit" when the provider returned no cache data, or shows a hit because the second call was simply faster.
**Why it happens:** `prompt_tokens_details` is absent for many providers/models, and provider sticky routing only activates after a real hit. Short demo prompts often fall below provider minimum cacheable lengths (e.g., OpenAI 1024 tokens, Anthropic 1024-4096).
**How to avoid:** Treat cache as present ONLY when `cached_tokens > 0` or `cache_write_tokens > 0`. Otherwise render "Cache/repeat: observed repeat latency/cost" with the delta. This is the OBS-04 fallback.
**Warning signs:** Repeat scenario reporting a cache hit on a ~10-token prompt, which cannot be cached by most providers.

### Pitfall 3: `SQLiteRunHistory` Round-Trip Corrupts New Fields and Sentinels

**What goes wrong:** `append()` stores `json.dumps(asdict(run.telemetry))`, so `Unavailable` becomes `{"label": "unavailable"}` and any new cache/trace fields are stored. But `_row_to_run()` rebuilds `TelemetryEvidence` with only the 7 original kwargs and passes `tel.get("latency_ms") or 0`, so (a) new fields are dropped on reload, (b) `Unavailable` sentinels come back as plain dicts, and (c) `fallback_evidence` is never persisted at all.
**Why it happens:** `asdict` + manual kwarg reconstruction without a dedicated (de)serializer.
**How to avoid:** Add explicit `TelemetryEvidence.to_dict()` / `from_dict()` (mapping `UNAVAILABLE` ↔ a sentinel string or `None`) and call them from `sqlite_store`; extend `_row_to_run` to pass all fields; persist `fallback_evidence` (or its JSON) too.
**Warning signs:** Reloaded runs show `{"label": "unavailable"}` in the model column, or cache/trace columns are empty after restart.
**Source:** [VERIFIED: src/openrouter_demo/sqlite_store.py:43-44 `json.dumps(asdict(run.telemetry)...)`, and `_row_to_run` at sqlite_store.py:82-103 reconstructing only 7 fields]

### Pitfall 4: Langfuse Trace Blocking or Failing the Run

**What goes wrong:** A Langfuse network/init error raises and surfaces as an inference failure, or `flush()` is called while an observation is still open.
**Why it happens:** Tracing is treated as core rather than optional; `flush()` does not end active observations.
**How to avoid:** Wrap trace creation in try/except returning `trace_status="failed"`; use the `start_as_current_observation` context manager (auto-ends on exit) and call `flush()` after the block. Never let a trace failure change `InferenceRun.status`.
**Warning signs:** Live runs fail only when `LANGFUSE_*` are set to a bad endpoint.

### Pitfall 5: `get_trace_url` Depends on `LANGFUSE_BASE_URL`

**What goes wrong:** The trace link points at a wrong/unreachable host.
**Why it happens:** `get_trace_url` builds `{base_url}/project/{project_id}/traces/{trace_id}` from the configured base URL; if `LANGFUSE_BASE_URL` is not the UI host (or points at the API-only endpoint), the link is wrong.
**How to avoid:** Document `LANGFUSE_BASE_URL` as the Langfuse UI root (e.g. `https://cloud.langfuse.com` or self-hosted UI). Render the link only when `trace_url` is non-null; otherwise show disabled copy.
**Source:** [VERIFIED: installed langfuse client.py `get_trace_url` returns `f"{self._base_url}/project/{project_id}/traces/{final_trace_id}"`]

### Pitfall 6: Streaming Cache Fields Arrive Only on the Final Chunk

**What goes wrong:** Extraction reads cache/usage from every chunk but the demo's short streams may carry `usage`/`prompt_tokens_details` only on the final chunk (before `[DONE]`).
**Why it happens:** Streaming responses deliver usage (and router metadata) on the terminal chunk.
**How to avoid:** The existing "last-seen wins" accumulation pattern already handles this — keep capturing `seen_*` values across chunks and only finalize into `StreamedResult` after the loop. Do not early-return on the first chunk that has usage.
**Source:** [VERIFIED: router-metadata docs — "For streaming responses, `openrouter_metadata` is delivered on the final chunk before `data: [DONE]`"]

### Pitfall 7: Langfuse `cost_details` Key Format Ambiguity

**What goes wrong:** Passing the wrong `cost_details` shape silently drops cost data.
**Why it happens:** The v4 signature types `cost_details: Dict[str, float]`, but the SDK README example passes `{"cost_amount": ..., "cost_currency": "USD"}` (a string value inside a float-typed dict). The accepted keys are ambiguous across versions.
**How to avoid:** Pass `usage_details={"prompt_tokens": ..., "completion_tokens": ...}` (verified) for tokens. For cost, either verify the accepted `cost_details` keys against the installed SDK before use, or attach cost to the observation's `metadata` (e.g. `{"cost_usd": ...}`). Add a `checkpoint:human-verify` if `cost_details` is used.
**Source:** [VERIFIED: installed 4.14.4 `start_as_current_observation` signature `cost_details: Optional[Dict[str, float]]`; CITED: langfuse-python README example `cost_details={"cost_amount": ..., "cost_currency": "USD"}`]

## Code Examples

Verified patterns from official sources and the installed SDK.

### OpenRouter Router Metadata Opt-In + Response

```python
# Source: [VERIFIED: openrouter.ai/docs/guides/features/router-metadata]
# Request header (add to client.py headers dict):
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "X-OpenRouter-Metadata": "enabled",   # opt-in; default is disabled
}

# Successful response (top-level openrouter_metadata, final streamed chunk):
# {
#   "model": "openai/gpt-4o-mini",
#   "openrouter_metadata": {
#     "requested": "openai/gpt-4o-mini",
#     "strategy": "direct",
#     "summary": "available=1, selected=OpenAI",
#     "attempt": 1,
#     "endpoints": { "total": 1, "available": [ {"provider": "OpenAI", "model": "openai/gpt-4o-mini", "selected": true} ] },
#     "attempts": [ {"provider": "OpenAI", "model": "openai/gpt-4o-mini", "status": 200} ]
#   }
# }
```

### Langfuse v4 Generation Trace

```python
# Source: [VERIFIED: installed langfuse 4.14.4 + langfuse-python README/autodocs]
from langfuse import get_client

client = get_client()  # LANGFUSE_PUBLIC_KEY / SECRET_KEY / BASE_URL

with client.start_as_current_observation(
    name="openrouter-inference",
    as_type="generation",
    model="openai/gpt-4o-mini",
    input={"prompt": "..."},
    output="streamed response",
    usage_details={"prompt_tokens": 42, "completion_tokens": 128},
) as gen:
    pass  # auto-ended on exit

client.flush()                       # short-lived app: flush events
trace_id = gen.trace_id              # 32-char lowercase hex
trace_url = client.get_trace_url(trace_id=trace_id)
# -> "{LANGFUSE_BASE_URL}/project/{project_id}/traces/{trace_id}"
```

### Cache Usage Object

```python
# Source: [VERIFIED: openrouter.ai/docs/features/prompt-caching]
# "usage": {
#   "prompt_tokens": 10339,
#   "completion_tokens": 60,
#   "total_tokens": 10399,
#   "prompt_tokens_details": {
#     "cached_tokens": 10318,     # tokens read from cache (cache hit)
#     "cache_write_tokens": 0     # tokens written to cache
#   }
# }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `X-OpenRouter-Experimental-Metadata` header | `X-OpenRouter-Metadata: enabled` | Legacy header still accepted | Use the new name; it is the documented, stable opt-in. [VERIFIED: router-metadata docs — "Legacy Header... still accepted"] |
| Cache fields `prompt_cache_hit_tokens` / `prompt_cache_miss_tokens` (legacy) | `usage.prompt_tokens_details.cached_tokens` / `cache_write_tokens` | Current docs | Detect cache via `prompt_tokens_details`; do not depend on the legacy names. [VERIFIED: prompt-caching docs] |
| Langfuse `trace()` / `generation()` / `span()` methods | Unified `start_observation()` / `start_as_current_observation(as_type=...)` | Langfuse Python SDK v4 | v3-style methods are gone in 4.14.4; use the unified API. [VERIFIED: installed 4.14.4] |
| Trace context via `get_trace_context()` | `observation.trace_id` attribute + `client.get_trace_url()` | v4.14.x | The `get_trace_context` helper from newer docs is absent in 4.14.4; use `.trace_id`. [VERIFIED: installed 4.14.4] |

**Deprecated/outdated:**
- `X-OpenRouter-Experimental-Metadata`: replaced by `X-OpenRouter-Metadata`.
- Legacy cache token names: superseded by `prompt_tokens_details`.
- Langfuse `trace()`/`generation()`/`span()`: removed in v4.

## Assumptions Log

> Claims tagged `[ASSUMED]` need user/planner confirmation before execution.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Streaming usage (and therefore cache fields) arrive on the final chunk without needing an explicit `stream_options: {"include_usage": true}`. Existing tests place usage on the final chunk and the code already captures it; OpenRouter docs say usage accompanies every response. | Common Pitfalls 6 | Cache fields silently missing from streaming if OpenRouter requires `stream_options`. Low risk — verify once live. |
| A2 | Langfuse `cost_details` accepted keys: the exact key set (`cost_amount`/`cost_currency` vs `input`/`output`/`total`) is unverified for 4.14.4. | Pitfall 7 | Cost dropped from traces if wrong keys are passed. |
| A3 | `LANGFUSE_BASE_URL` is expected to be the Langfuse UI root (not API-only) for `get_trace_url` to produce a clickable link. | Pitfall 5 | Broken trace links in the demo. |
| A4 | Legacy cache field names (`prompt_cache_hit_tokens`/`prompt_cache_miss_tokens`) may still appear from some providers even though current docs don't document them; detection should not rely on them. | State of the Art | Missed cache signals on legacy providers (non-blocking). |

**If this table is empty:** not applicable — four assumptions logged above.

## Open Questions (RESOLVED)

1. **SQLite vs in-memory history for OBS-07**
   - What we know: `app.py:16-18` wires `SQLiteRunHistory(db_path="data/runs.db")`; `REQUIREMENTS.md` Out of Scope says "Database persistence — Runtime history can stay in memory"; `RunHistory` (in-memory) is still used by all tests.
   - What's unclear: whether persistence across restart is intended or accidental.
   - Recommendation: keep `SQLiteRunHistory` (it's already wired and gives OBS-07 persistence), but fix the round-trip. If the user prefers in-memory, reverting `app.py` to `RunHistory()` is a one-line change.
   - RESOLVED: 04-03.1 — keep `SQLiteRunHistory` and fix its round-trip.

2. **`cost_details` key format for Langfuse**
   - What we know: type sig `Dict[str, float]` vs README example `cost_amount`/`cost_currency`.
   - What's unclear: accepted keys in 4.14.4.
   - Recommendation: use `usage_details` for tokens; put cost in `metadata` or gate `cost_details` behind a verify checkpoint.
   - RESOLVED: 04-01.2 — use `usage_details` for tokens; put cost in `metadata` (opt out of ambiguous `cost_details` keys).

3. **Repeat scenario shape**
   - What we know: `data-model.md` names `repeat_observation`; screen-spec lists a "Cache / repeat" telemetry row and a "Repeat previous prompt" action.
   - What's unclear: one scenario that runs the prompt twice internally vs a "Repeat" button that re-runs the last run and diffs against history.
   - Recommendation: implement both cheaply — a `run_repeat_scenario` for the deterministic two-run observation, plus a "Repeat" button that re-submits the last prompt/strategy.
   - RESOLVED: 04-02.1 + 04-02.2 — implement `run_repeat_scenario` (two-run observation) plus a Repeat action in the UI.

4. **Should `telemetry_schema.py` be removed or reconciled?**
   - What we know: it's unused dead code with a competing `RunRecord`/`FallbackAttempt` schema.
   - Recommendation: remove it (or fold it into a docstring on `TelemetryEvidence`) to keep one source of truth; confirm with the planner to keep the change surgical.
   - RESOLVED: 04-03.3 — remove `telemetry_schema.py` (verified unused; keep one source of truth).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | runtime | ✓ | 3.13 (venv) | — |
| uv | install/run | ✓ | (used throughout) | — |
| NiceGUI | UI | ✓ | ≥3.16.0 | — |
| httpx | client | ✓ | ≥0.28.1 | — |
| langfuse | OBS-05/06 | ✓ | 4.14.4 | tracing disabled when creds absent |
| pytest | tests | ✓ | ≥9.1.1 | — |
| ruff | lint | ✓ | ≥0.16.3 | — |
| `OPENROUTER_API_KEY` | live inference | ✗ (not exported by default) | — | UI shows setup guidance; tests use MockTransport |
| `LANGFUSE_*` (3 vars) | tracing | ✗ (optional) | — | `trace_status="disabled"`, visible in UI |

**Missing dependencies with no fallback:**
- `OPENROUTER_API_KEY` — required for live inference; absent in a fresh env. App already shows setup guidance (SETUP-05); tests are network-free.

**Missing dependencies with fallback:**
- `LANGFUSE_*` — optional; the disabled-tracing path is the fallback (OBS-06).

## Validation Architecture

Nyquist validation is enabled (`.planning/config.json` `workflow.nyquist_validation: true`). All Phase 4 behavior is unit-testable with `httpx.MockTransport` and injected fake streams — no live network needed.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest ≥9.1.1 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` — `testpaths = ["tests"]`, `pythonpath = ["src"]` [VERIFIED: pyproject.toml:20-22] |
| Quick run command | `uv run pytest tests/test_telemetry.py tests/test_client.py -q` |
| Full suite command | `uv run pytest` |
| Lint gate | `uv run ruff check .` |

### Testable Validation Dimensions

| Dimension | Observable/Verifiable Check | Test Type | Automated Command | File Exists? |
|-----------|-----------------------------|-----------|-------------------|-------------|
| Telemetry normalization (OBS-01) | `TelemetryEvidence` for every completed run has model/provider/latency/tokens/cost/cache/trace fields; `Unavailable` ≠ 0 (truthiness False, `!= 0`) | unit | `pytest tests/test_telemetry.py::test_normalize_telemetry_fields -x` | ❌ Wave 0 |
| Cache-metadata honesty (OBS-03/OBS-04) | cache row populated only when `cached_tokens>0` or `cache_write_tokens>0`; otherwise repeat latency/cost delta shown; a fast repeat without cache data is NOT labeled "hit" | unit | `pytest tests/test_repeat.py -x` | ❌ Wave 0 |
| Langfuse toggle behavior (OBS-05/OBS-06) | `config.langfuse_ready=False` → `trace_status="disabled"`, no `get_client()` call; `langfuse_ready=True` → trace id/url captured; a trace exception → `trace_status="failed"` and run still succeeds | unit | `pytest tests/test_telemetry.py::test_trace_toggle -x` | ❌ Wave 0 |
| Router metadata absence (OBS-02) | header `X-OpenRouter-Metadata: enabled` present in request; missing `openrouter_metadata` in response → `UNAVAILABLE`, not fabricated | unit | `pytest tests/test_client.py::test_metadata_header_and_absence -x` | ❌ Wave 0 |
| Repeat/cache scenario assertions | two-run scenario yields both attempts + cache-or-repeat observation; primary success edge case handled | unit | `pytest tests/test_scenarios.py -x` | ✅ (extend) |
| Persistence round-trip (OBS-07) | saved+reloaded run preserves `Unavailable` sentinels and cache/trace fields | unit | `pytest tests/test_sqlite_store.py -x` | ❌ Wave 0 |
| UI comparison (OBS-07) | history rows include Cache and Trace columns; comparison grid renders ≥N runs | smoke/unit | `pytest tests/test_ui.py -x` | ✅ (extend) |
| Regression: Phase 1 guards | Langfuse guard updated to allow conditional tracing; no `from fastapi`, no core `sqlite3` imports | unit | `pytest tests/test_phase1_guards.py -x` | ✅ (extend) |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/<touched-file> -q`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** `uv run pytest` AND `uv run ruff check .` both green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_telemetry.py` — normalization + Langfuse toggle behavior
- [ ] `tests/test_repeat.py` — cache-honesty assertions (present vs absent)
- [ ] `tests/test_sqlite_store.py` — round-trip preserves sentinels + new fields
- [ ] `tests/test_client.py` — extend: metadata header + cache/absence extraction
- [ ] `tests/test_phase1_guards.py` — update Langfuse guard (currently forbids `get_client(`)

## Security Domain

`security_enforcement` is enabled (`.planning/config.json`), ASVS level 1.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Local demo; no user accounts (out of scope) |
| V3 Session Management | no | Local single-user NiceGUI app |
| V4 Access Control | no | No multi-tenancy or roles |
| V5 Input Validation | yes | Explicit prompt non-empty check (already `_run_inference`); validate Langfuse/OpenRouter config presence before use; never trust response payload shape (existing `isinstance` guards in `_extract_*`) |
| V6 Cryptography | no | No cryptographic operations; secrets held in env vars only |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Secret leakage in UI/telemetry/traces | Information Disclosure | Show readiness only, never values (existing `_status`); never pass `api_key` into Langfuse input/metadata |
| Fabricated cache/trace claims | Spoofing | Only report cache when `prompt_tokens_details` proves it; only report trace when the SDK returned an id/url |
| Untrusted model output rendering | Spoofing / Injection | NiceGUI label text is escaped; keep raw response out of comparison columns |
| Tracing failure taking down inference | Denial of Service | try/except around Langfuse; `trace_status="failed"` never changes `InferenceRun.status` |
| SQL injection in history store | Tampering | Parameterized SQL already used in `sqlite_store.py` (`?` placeholders) [VERIFIED: sqlite_store.py:47-48] |

## Sources

### Primary (HIGH confidence)

- OpenRouter Router Metadata docs — https://openrouter.ai/docs/guides/features/router-metadata — opt-in header, response shape, cache-hit stripping, error envelopes, legacy header.
- OpenRouter Prompt Caching docs — https://openrouter.ai/docs/features/prompt-caching — `prompt_tokens_details.cached_tokens` / `cache_write_tokens`, sticky routing, per-provider minimums.
- Langfuse Python SDK v4 — Context7 `/langfuse/langfuse-python` — unified observation API, README/autodocs examples.
- Installed `langfuse` 4.14.4 package source (`.venv/lib/python3.13/site-packages/langfuse/_client/`) — verified `get_client`, `start_as_current_observation` signature, `LangfuseObservationWrapper.trace_id`/`.id`, `get_trace_url` format, absence of `get_trace_context`/`trace()`/`generation()`.
- In-repo source files (verbatim line-cited throughout): `models.py`, `client.py`, `config.py`, `telemetry.py`, `telemetry_schema.py`, `sqlite_store.py`, `ui.py`, `app.py`, `pyproject.toml`, `tests/test_phase1_guards.py`.

### Secondary (MEDIUM confidence)

- `docs/specs/data-model.md` — target `TelemetryEvidence` extension fields (`cache_status`, `repeat_observation`, `fallback_used`, `trace_status`, `trace_url`).
- `docs/specs/research.md` — prior Langfuse-optionality and direct-HTTP decisions.
- `docs/ux/screen-spec.md` — Cache/repeat and Trace telemetry rows, "Repeat previous prompt" action.
- `.planning/telemetry-schema.md` — aspirational normalized record (id/timestamp/strategy/provider/model/latency/tokens/cost/fallback_attempts/trace_id/raw_response).

### Tertiary (LOW confidence)

- Legacy cache field names `prompt_cache_hit_tokens` / `prompt_cache_miss_tokens` — referenced in the task prompt; not found in current OpenRouter docs, treated as superseded (Assumption A4).
- `stream_options.include_usage` requirement for streaming usage — not directly verified against OpenRouter docs (Assumption A1).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every package verified against `pyproject.toml` and the installed environment.
- Architecture: HIGH — grounded in the existing `models.py`/`client.py`/`scenarios.py`/`sqlite_store.py`/`ui.py` split, read this session.
- Pitfalls: HIGH — several verified against live source (Phase 1 guard test, SQLite round-trip, Langfuse 4.14.4 API), with two flagged as assumptions.

**Research date:** 2026-08-19
**Valid until:** 2026-09-19 (30 days; Langfuse SDK and OpenRouter cache/metadata fields are fast-moving — re-verify before Phase 6 if more than ~30 days elapse)
