---
phase: 03-routing-and-fallback-demo
status: complete
sources:
  - .planning/STATE.md
  - .planning/ROADMAP.md
  - .planning/REQUIREMENTS.md
  - .planning/PROJECT.md
  - .planning/research/FEATURES.md
  - .planning/research/PITFALLS.md
  - .planning/research/STACK.md
  - .planning/config.json
  - docs/ux/screen-spec.md
  - docs/ux/ui-ux-plan.md
  - docs/ux/demo-narrative.md
  - docs/ux/technical-walkthrough.md
  - docs/design/DESIGN-light.md
  - docs/specs/failure-tree.md
  - docs/specs/research.md
  - docs/specs/data-model.md
  - docs/specs/acceptance-criteria.md
  - .planning/phases/02-streaming-inference-evidence/02-RESEARCH.md
  - .planning/phases/02-streaming-inference-evidence/02-UI-SPEC.md
  - .planning/phases/02-streaming-inference-evidence/02-01-SUMMARY.md
  - src/openrouter_demo/routing.py
  - src/openrouter_demo/client.py
  - src/openrouter_demo/models.py
  - src/openrouter_demo/scenarios.py
  - src/openrouter_demo/ui.py
  - src/openrouter_demo/history.py
  - src/openrouter_demo/config.py
  - src/openrouter_demo/telemetry.py
  - app.py
  - tests/test_client.py
  - tests/test_ui.py
  - tests/test_imports.py
  - tests/test_phase1_guards.py
  - pyproject.toml
  - OpenRouter Provider Routing docs (https://openrouter.ai/docs/guides/routing/provider-selection)
  - OpenRouter Model Fallbacks docs (https://openrouter.ai/docs/guides/routing/model-fallbacks)
created: 2026-08-19
---

# Phase 03 Research: Routing and Fallback Demo

## Summary

Phase 3 adds three capabilities to the existing Phase 2 streaming console: (1) strategy selection with reviewer-facing tradeoff explanations, (2) provider routing parameters sent to OpenRouter for each strategy, and (3) a reproducible fallback scenario that preserves primary failure evidence when fallback succeeds.

The OpenRouter Chat Completions API supports a `provider` object in the request body with `sort` (string or object), `allow_fallbacks` (boolean), `order` (string[]), `only`, `ignore`, `preferred_max_latency`, `preferred_min_throughput`, `max_price`, `require_parameters`, `data_collection`, `quantizations`, `zdr`, and `enforce_distillable_text` fields. The three demo strategies map cleanly: default uses no `provider` key (OpenRouter load-balances by price), cost uses `{"sort": "price"}`, and latency uses `{"sort": "latency"}`. [VERIFIED: openrouter.ai/docs/guides/routing/provider-selection]

For the fallback scenario, the critical requirement is ROUTE-05 and ROUTE-06: both the failed primary attempt AND the successful fallback must be visible. OpenRouter's server-side model fallback (the `models` array field) handles fallback transparently — the client only sees the final successful response with the ultimate model name, with no explicit failure event for the primary. This is insufficient for the demo's evidence-preservation requirement. Instead, the recommended approach is **client-side two-attempt orchestration**: a primary request with a nonexistent model and `allow_fallbacks: false` (deterministic 404, zero cost), followed by a fallback request with the real strategy (success, normal cost). Both attempts produce explicit, separate evidence records. [VERIFIED: openrouter.ai/docs/guides/routing/model-fallbacks — "If the model you selected returns an error, OpenRouter will try to use the fallback model instead" — server-side, no primary failure event exposed to client]

**Primary recommendation:** Implement strategies as inspectable policy objects in `routing.py` with `provider_preferences` emitted by `strategy_payload()`. Implement the fallback scenario as a two-attempt client-side function in `scenarios.py` using a dedicated `FALLBACK_PRIMARY_STRATEGY` (nonexistent model, `allow_fallbacks: false`). Add `AttemptRecord` and `FallbackEvidence` types to `models.py`. Add `Status.FALLBACK_SUCCEEDED` to distinguish fallback success from plain success. Wire a strategy selector and fallback toggle into the NiceGUI UI.

**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ROUTE-01 | User can choose at least default, cost-oriented, and latency-oriented routing strategies. | `RoutingStrategy` dataclass and `ROUTING_STRATEGY_LABELS` already define all three names. Add `COST_STRATEGY` and `LATENCY_STRATEGY` instances with `provider_preferences` for `sort: "price"` and `sort: "latency"`. UI adds a selector bound to a strategy registry. |
| ROUTE-02 | UI explains each strategy tradeoff before a run. | Each `RoutingStrategy` already has a `description` field. Screen spec defines exact copy for each strategy. UI renders the description of the selected strategy before the run starts. |
| ROUTE-03 | Completed run shows the selected strategy and the actual route/model evidence returned by the request. | `InferenceRun.strategy_name` already stores the selected strategy. `TelemetryEvidence.model` and `TelemetryEvidence.provider` capture actual returned route. `stream_chat_completion` already extracts these from SSE chunks. No new extraction logic needed. |
| ROUTE-04 | User can trigger a reproducible fallback scenario. | Implement `run_fallback_scenario()` in `scenarios.py` using a deterministic primary failure (nonexistent model + `allow_fallbacks: false`). UI adds a "Simulate primary route failure" toggle that routes the run through the scenario function instead of the normal stream. |
| ROUTE-05 | Fallback scenario shows the failed primary attempt, failure reason or timeout, fallback route, and final result. | Two-attempt client-side orchestration produces explicit `AttemptRecord` for each attempt: primary (status=FAILED, error_message from HTTP 404) and fallback (status=SUCCEEDED, telemetry with model/provider). `FallbackEvidence` type wraps both. UI renders both in the telemetry panel. |
| ROUTE-06 | Successful fallback does not hide primary failure evidence. | `InferenceRun` gains `fallback_evidence: FallbackEvidence | None`. When present, UI shows primary failure details alongside fallback success. `Status.FALLBACK_SUCCEEDED` distinguishes from plain `SUCCEEDED`. Tests assert both attempt records are present and rendered. |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Strategy selection (UI control) | Browser / Client (NiceGUI) | — | UI state owns which strategy is selected; selector is a client-side control |
| Strategy payload construction | API / Backend (`routing.py`) | — | Strategies are inspectable policy objects; `strategy_payload()` emits the OpenRouter request body |
| Provider routing parameters | API / Backend (`routing.py`) | — | `provider_preferences` dict per strategy, emitted into request body by `strategy_payload()` |
| Fallback scenario orchestration | API / Backend (`scenarios.py`) | — | Two-attempt sequence with explicit failure capture; owns the deterministic failure trigger |
| Fallback evidence modeling | API / Backend (`models.py`) | — | `AttemptRecord` and `FallbackEvidence` are typed data; `UNAVAILABLE` sentinels preserved |
| Streaming + metadata extraction | API / Backend (`client.py`) | — | Already owns SSE parsing, model/provider/usage extraction, error types |
| Fallback evidence rendering | Browser / Client (`ui.py`) | — | UI renders telemetry rows, response status, history rows with fallback column |
| Run history | Browser / Client (`ui.py` + `history.py`) | — | In-memory bounded history; UI renders rows with strategy and fallback columns |

## Standard Stack

### Core

No new packages. Phase 3 uses the existing Phase 1/2 stack exclusively.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python 3.12+ | ≥3.12 | Application runtime | Project constraint [VERIFIED: pyproject.toml:5 `requires-python = ">=3.12"`] |
| NiceGUI | ≥3.16.0 | Local browser UI | Project constraint [VERIFIED: pyproject.toml:8 `"nicegui>=3.16.0"`] |
| httpx | ≥0.28.1 | Async HTTP for OpenRouter | Project constraint [VERIFIED: pyproject.toml:9 `"httpx>=0.28.1"`] |
| pytest | ≥9.1.1 | Focused tests | Project constraint [VERIFIED: pyproject.toml:14 `"pytest>=9.1.1"`] |
| Ruff | ≥0.16.3 | Linting and formatting | Project constraint [VERIFIED: pyproject.toml:15 `"ruff>=0.16.3"`] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx.MockTransport | (built into httpx) | No-network test transport | All client/scenario tests — already used in `tests/test_client.py` [VERIFIED: tests/test_client.py:14 `_client_with(handler)`] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Client-side two-attempt fallback | OpenRouter `models` array (server-side) | Server-side fallback is invisible to the client — no primary failure event, only final success. Fails ROUTE-05/06. |
| Client-side two-attempt fallback | Simulated local failure (no network) | More controlled but less authentic. Doesn't prove real OpenRouter error handling. Use as fallback if network is unavailable. |
| `sort: "price"` for cost strategy | `:floor` model slug suffix | Equivalent per docs, but `sort` is more inspectable in the request body for the interview demo. [CITED: openrouter.ai/docs/guides/routing/provider-selection] |
| `sort: "latency"` for latency strategy | `preferred_max_latency` percentile cutoffs | `sort` is simpler and sufficient for the demo. `preferred_max_latency` could be a Phase 4 enhancement. |

**Installation:**

```bash
# No new packages to install. Existing environment is sufficient.
uv sync
```

**Version verification:** All packages already installed and verified in Phase 1/2. No version changes needed.

## Package Legitimacy Audit

No new packages introduced in this phase. All dependencies are existing from Phase 1/2 and were verified during those phases.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| nicegui | PyPI | existing | existing | github.com/zauberzeug/nicegui | OK | Approved (Phase 1) |
| httpx | PyPI | existing | existing | github.com/encode/httpx | OK | Approved (Phase 1) |
| pytest | PyPI | existing | existing | github.com/pytest-dev/pytest | OK | Approved (Phase 1) |
| ruff | PyPI | existing | existing | github.com/astral-sh/ruff | OK | Approved (Phase 1) |
| langfuse | PyPI | existing | existing | github.com/langfuse/langfuse-python | OK | Approved (Phase 1) |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```text
User selects strategy + optional fallback toggle
        │
        ▼
┌──────────────────────────────────────────┐
│ ui.py: run_request()                     │
│  Reads strategy selector + toggle state  │
└──────────┬───────────────────────────────┘
           │
           ├─ toggle OFF ──► _run_inference(strategy)
           │                    │
           │                    ▼
           │              stream_chat_completion(strategy)
           │                    │
           │                    ▼
           │              Single StreamedResult
           │                    │
           │                    ▼
           │              InferenceRun(status=SUCCEEDED)
           │
           └─ toggle ON ──► run_fallback_scenario(strategy)
                                │
                                ▼
                    ┌──────────────────────┐
                    │ Attempt 1 (primary)  │
                    │ FALLBACK_PRIMARY_    │
                    │ STRATEGY             │
                    │ model="nonexistent"  │
                    │ allow_fallbacks=false│
                    └──────────┬───────────┘
                               │
                          HTTP 404 error
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Attempt 2 (fallback) │
                    │ Selected strategy    │
                    │ allow_fallbacks=true │
                    └──────────┬───────────┘
                               │
                          SSE stream
                               │
                               ▼
                    InferenceRun(
                      status=FALLBACK_SUCCEEDED,
                      fallback_evidence=FallbackEvidence(
                        primary=AttemptRecord(FAILED, ...),
                        fallback=AttemptRecord(SUCCEEDED, ...)
                      )
                    )
                               │
                               ▼
                    ui.py renders:
                    - Response: "Completed via fallback
                      route after primary route failed."
                    - Telemetry: primary status + fallback
                      status + model/provider
                    - History: strategy + fallback=Yes
```

### Recommended Project Structure

```text
src/openrouter_demo/
├── routing.py       # Add COST_STRATEGY, LATENCY_STRATEGY, FALLBACK_PRIMARY_STRATEGY; update strategy_payload()
├── models.py        # Add Status.FALLBACK_SUCCEEDED, AttemptRecord, FallbackEvidence; add fallback_evidence to InferenceRun
├── scenarios.py     # Replace stub with run_fallback_scenario() — two-attempt orchestration
├── client.py        # No changes needed (already supports model param and strategy_payload)
├── ui.py            # Add strategy selector, fallback toggle, fallback evidence rendering, history fallback column
├── history.py       # No changes needed (stores InferenceRun which now carries fallback_evidence)
├── config.py        # No changes
└── telemetry.py     # No changes (Phase 4 scope)
tests/
├── test_routing.py  # NEW: strategy payload tests for each strategy
├── test_scenarios.py # NEW: fallback scenario tests with injected streams
├── test_ui.py       # EXTEND: strategy selector, fallback toggle, fallback evidence rendering
├── test_client.py   # No changes needed
├── test_imports.py  # EXTEND: verify new types import, update scenario stub expectation
└── test_phase1_guards.py # No changes
```

### Pattern 1: Strategy as Inspectable Policy Object

**What:** Each routing strategy is a frozen dataclass instance with a name, description, model, and provider_preferences dict. The `strategy_payload()` function converts it to an OpenRouter request body fragment.

**When to use:** Always — strategies should never be scattered conditionals in UI or client code.

**Example:**
```python
# Source: [VERIFIED: src/openrouter_demo/routing.py:1-34 — existing pattern]
# Extended for Phase 3:

COST_STRATEGY = RoutingStrategy(
    name="cost",
    description="Prefer lower-cost model/provider choices. Validate quality before adopting.",
    model="openai/gpt-4o-mini",
    provider_preferences={"sort": "price"},
)

LATENCY_STRATEGY = RoutingStrategy(
    name="latency",
    description="Prefer faster routes for interactive use cases.",
    model="openai/gpt-4o-mini",
    provider_preferences={"sort": "latency"},
)

FALLBACK_PRIMARY_STRATEGY = RoutingStrategy(
    name="custom",
    description="Simulated primary route failure for demo fallback scenario.",
    model="nonexistent/fake-model-for-demo",
    provider_preferences={"allow_fallbacks": False},
)

def strategy_payload(strategy: RoutingStrategy) -> dict[str, object]:
    payload: dict[str, object] = {"model": strategy.model}
    if strategy.provider_preferences is not None:
        payload["provider"] = strategy.provider_preferences
    return payload
```

### Pattern 2: Two-Attempt Client-Side Fallback Orchestration

**What:** The fallback scenario makes two sequential API calls: a primary that deterministically fails, then a fallback that succeeds. Both produce explicit evidence records.

**When to use:** When the demo requires visible primary failure evidence (ROUTE-05/06). Do NOT use OpenRouter's server-side `models` array fallback for this — it hides the primary failure.

**Example:**
```python
# Source: [ASSUMED — new pattern for Phase 3, following existing stream_chat_completion injection pattern]

async def run_fallback_scenario(
    prompt: str,
    *,
    fallback_strategy: RoutingStrategy,
    api_key: str,
    stream_fn: StreamFn = stream_chat_completion,
) -> AsyncIterator[StreamChunk | StreamedResult | FallbackResult]:
    # Attempt 1: primary (deterministic failure)
    primary_error: OpenRouterError | None = None
    primary_start = time.monotonic()
    try:
        async for _event in stream_fn(
            prompt,
            strategy=FALLBACK_PRIMARY_STRATEGY,
            api_key=api_key,
        ):
            pass  # primary should fail before yielding any chunks
    except OpenRouterError as exc:
        primary_error = exc
    primary_latency_ms = int((time.monotonic() - primary_start) * 1000)

    if primary_error is None:
        # Edge case: primary unexpectedly succeeded — treat as normal run
        yield FallbackResult(primary_succeeded_unexpectedly=True, ...)
        return

    primary_record = AttemptRecord(
        model=FALLBACK_PRIMARY_STRATEGY.model,
        provider=UNAVAILABLE,
        status=Status.FAILED,
        error_message=str(primary_error),
        latency_ms=primary_latency_ms,
    )

    # Attempt 2: fallback (real strategy, should succeed)
    fallback_result: StreamedResult | None = None
    async for event in stream_fn(
        prompt,
        strategy=fallback_strategy,
        api_key=api_key,
    ):
        if isinstance(event, StreamChunk):
            yield event  # stream chunks to UI for progressive display
        elif isinstance(event, StreamedResult):
            fallback_result = event

    # Yield combined fallback result with both attempt records
    yield FallbackResult(
        primary=primary_record,
        fallback=fallback_result,
        simulated=True,
    )
```

### Pattern 3: Injected Async Streams for No-Network Tests

**What:** Test functions inject fake async streams that yield `StreamChunk` and `StreamedResult` objects. No test instantiates `httpx.AsyncClient` or calls live OpenRouter.

**When to use:** All tests for UI handlers and scenario functions.

**Example:**
```python
# Source: [VERIFIED: tests/test_ui.py:17-26 — existing Phase 2 pattern]
async def fake_stream(*_args, **_kwargs) -> AsyncIterator[StreamChunk | StreamedResult]:
    yield StreamChunk("Hello ")
    yield StreamChunk("there")
    yield StreamedResult(
        text="Hello there",
        model="openai/gpt-4o-mini",
        provider="OpenAI",
        prompt_tokens=3, completion_tokens=4, total_tokens=7,
        cost_usd=0.001, latency_ms=321,
    )

# For fallback scenario tests, inject two different streams:
async def failing_primary_stream(*_args, **_kwargs) -> AsyncIterator[...]:
    raise OpenRouterHTTPError("Model not found", status_code=404, partial_text="")

async def success_fallback_stream(*_args, **_kwargs) -> AsyncIterator[...]:
    yield StreamChunk("Fallback ")
    yield StreamChunk("response")
    yield StreamedResult(text="Fallback response", ...)
```

### Anti-Patterns to Avoid

- **Server-side `models` array for fallback demo:** OpenRouter's `models: ["bad-model", "good-model"]` handles fallback invisibly. The client only sees the final success. This fails ROUTE-05 (no visible primary failure) and ROUTE-06 (primary failure is hidden). [VERIFIED: openrouter.ai/docs/guides/routing/model-fallbacks — "If the model you selected returns an error, OpenRouter will try to use the fallback model instead" — no primary failure event exposed]

- **Collapsing fallback into a single status:** Setting `status=SUCCEEDED` for a fallback run hides that fallback occurred. Use `Status.FALLBACK_SUCCEEDED` to make the state explicit. [CITED: docs/ux/screen-spec.md — "Status: Shows idle, streaming, success, fallback success, or failed"]

- **Stringifying `UNAVAILABLE` in fallback evidence:** The failed primary attempt will have `UNAVAILABLE` for tokens, cost, and possibly provider. These must remain as `UNAVAILABLE` sentinels until rendered by format helpers, never coerced to zero or empty string. [VERIFIED: .planning/research/PITFALLS.md — Pitfall 1: Claiming Metadata That Was Not Returned]

- **Scattering strategy conditionals in UI code:** Strategy-to-payload mapping belongs in `routing.py`, not in `ui.py` event handlers. UI reads the selected strategy's description and passes the strategy object to the stream/scenario function.

- **Over-constraining the fallback primary:** Using `provider: {"only": ["nonexistent"]}` with a real model may not deterministically fail if OpenRouter treats unknown providers differently. Use a nonexistent model with `allow_fallbacks: false` for maximum reproducibility.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Provider routing parameters | Custom routing logic in Python | OpenRouter `provider` object in request body | OpenRouter handles provider selection, load balancing, and fallback server-side. The demo sends preferences, not routing logic. [VERIFIED: openrouter.ai/docs/guides/routing/provider-selection] |
| Model fallback | Custom retry loop with model swapping | Client-side two-attempt orchestration (for demo evidence) OR OpenRouter `models` array (for production) | The demo needs explicit primary failure evidence, so a simple two-attempt sequence is sufficient. Don't build a general retry framework. |
| Strategy descriptions | Generated or templated text | Hardcoded descriptions from screen spec | The screen spec defines exact copy. Don't generate tradeoff language dynamically. [CITED: docs/ux/screen-spec.md — strategy option labels and descriptions] |
| SSE parsing | Custom SSE parser | Existing `stream_chat_completion` in `client.py` | Already handles `data:` lines, JSON parsing, metadata extraction, error events. [VERIFIED: src/openrouter_demo/client.py:33-81] |
| Metadata formatting | Ad-hoc string conversion | Existing `_format_metadata`, `_format_tokens`, `_format_cost`, `_format_latency` helpers | Already tested and consistent. Fallback evidence uses the same helpers. [VERIFIED: src/openrouter_demo/ui.py:34-53] |

**Key insight:** Phase 3 adds routing policy and fallback orchestration, not new infrastructure. The existing client, models, history, and formatting helpers are sufficient. The main work is in `routing.py` (new strategy instances + payload), `scenarios.py` (fallback orchestration), `models.py` (new types), and `ui.py` (new controls + rendering).

## Common Pitfalls

### Pitfall 1: Silent or Hidden Fallback

**What goes wrong:** A fallback succeeds, but the UI only shows a successful final answer. The primary failure is invisible.
**Why it happens:** Error handling collapses multiple attempts into one final status, or server-side fallback (OpenRouter `models` array) doesn't expose the primary failure.
**How to avoid:** Use client-side two-attempt orchestration. Store `FallbackEvidence` with both `AttemptRecord` objects on the `InferenceRun`. Use `Status.FALLBACK_SUCCEEDED` (not `SUCCEEDED`) when fallback occurs. Render primary failure details in the telemetry panel.
**Warning signs:** Tests pass but fallback runs look identical to normal success runs in the UI. [VERIFIED: .planning/research/PITFALLS.md — Pitfall 2: Silent or Hidden Fallback]

### Pitfall 2: Strategy Payload Omitting the Provider Object

**What goes wrong:** `strategy_payload()` returns only `{"model": strategy.model}` and never includes the `provider` key, so cost/latency sorting preferences are never sent to OpenRouter.
**Why it happens:** The current implementation [VERIFIED: src/openrouter_demo/routing.py:33-34] ignores `provider_preferences`. If the planner doesn't update `strategy_payload()`, the strategies are cosmetic labels with no actual routing effect.
**How to avoid:** Update `strategy_payload()` to include `provider` from `strategy.provider_preferences` when it's not `None`. Test that cost strategy payload contains `{"sort": "price"}` and latency contains `{"sort": "latency"}`.
**Warning signs:** Cost and latency runs produce identical telemetry to default runs.

### Pitfall 3: Breaking the Existing ROUTING_STRATEGY_LABELS Test

**What goes wrong:** Adding or renaming strategy labels breaks `test_imports.py::test_routing_labels_do_not_claim_provider_results`.
**Why it happens:** The test asserts an exact dict equality: `{"default": "Default", "cost": "Cost optimized", "latency": "Latency optimized", "custom": "Custom"}`. [VERIFIED: tests/test_imports.py:46-51]
**How to avoid:** Do not change `ROUTING_STRATEGY_LABELS`. The labels already include all four strategy names. Phase 3 adds strategy *instances* (COST_STRATEGY, LATENCY_STRATEGY), not new label entries.
**Warning signs:** `test_imports.py` fails after adding strategy instances.

### Pitfall 4: Fallback Primary Actually Succeeds

**What goes wrong:** The "nonexistent" model accidentally exists on OpenRouter, or OpenRouter's default `allow_fallbacks: true` routes to a fallback provider even with a bad model.
**Why it happens:** Model namespace is large; a model that seems fake might exist. And `allow_fallbacks` defaults to `true`, so even with a bad model, OpenRouter might try alternatives.
**How to avoid:** Use `provider_preferences={"allow_fallbacks": False}` explicitly on the primary strategy. Use an obviously fake model slug like `nonexistent/fake-model-for-demo`. Handle the edge case where primary unexpectedly succeeds (treat as normal run, don't fabricate failure).
**Warning signs:** Fallback scenario shows `SUCCEEDED` instead of `FALLBACK_SUCCEEDED` during manual testing.

### Pitfall 5: Fallback Toggle State Leaking Into Normal Runs

**What goes wrong:** The "Simulate primary route failure" toggle is on, but the user expects a normal run. Or the toggle state persists across runs incorrectly.
**Why it happens:** UI state management doesn't read the toggle at the right time, or the toggle doesn't reset after a run.
**How to avoid:** Read toggle state at the start of `run_request()`. The toggle is a per-run setting — it should persist across runs (user may want to run multiple fallback demos) but should be clearly labeled. The screen spec says "Simulate primary route failure" with helper text "For a reproducible demo. The UI will label this as simulated." [CITED: docs/ux/screen-spec.md:169-173]

### Pitfall 6: Cost Explosion From Fallback Scenario

**What goes wrong:** The fallback scenario makes two API calls per run, doubling cost.
**Why it happens:** Both attempts call the real OpenRouter API.
**How to avoid:** The primary attempt uses a nonexistent model with `allow_fallbacks: false` — it fails immediately with a 404 and generates zero tokens, so it's free. Only the fallback attempt costs tokens. Total cost per fallback run equals one normal run. [VERIFIED: openrouter.ai/docs/guides/routing/model-fallbacks — "Requests are priced using the model that was ultimately used"]

## Code Examples

### Strategy Registry and Payload

```python
# Source: [VERIFIED: src/openrouter_demo/routing.py:1-34 existing; extended per VERIFIED openrouter.ai/docs/guides/routing/provider-selection]

from dataclasses import dataclass
from typing import Literal

StrategyName = Literal["default", "cost", "latency", "custom"]

ROUTING_STRATEGY_LABELS: dict[StrategyName, str] = {
    "default": "Default",
    "cost": "Cost optimized",
    "latency": "Latency optimized",
    "custom": "Custom",
}

# Do NOT change the labels dict — test_imports.py asserts exact equality.
# [VERIFIED: tests/test_imports.py:46-51]

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

COST_STRATEGY = RoutingStrategy(
    name="cost",
    description="Prefer lower-cost model/provider choices. Validate quality before adopting.",
    model="openai/gpt-4o-mini",
    provider_preferences={"sort": "price"},
)

LATENCY_STRATEGY = RoutingStrategy(
    name="latency",
    description="Prefer faster routes for interactive use cases.",
    model="openai/gpt-4o-mini",
    provider_preferences={"sort": "latency"},
)

FALLBACK_PRIMARY_STRATEGY = RoutingStrategy(
    name="custom",
    description="Simulated primary route failure for demo fallback scenario.",
    model="nonexistent/fake-model-for-demo",
    provider_preferences={"allow_fallbacks": False},
)

STRATEGIES: dict[StrategyName, RoutingStrategy] = {
    "default": DEFAULT_STRATEGY,
    "cost": COST_STRATEGY,
    "latency": LATENCY_STRATEGY,
}

def strategy_payload(strategy: RoutingStrategy) -> dict[str, object]:
    payload: dict[str, object] = {"model": strategy.model}
    if strategy.provider_preferences is not None:
        payload["provider"] = strategy.provider_preferences
    return payload
```

### New Model Types

```python
# Source: [VERIFIED: src/openrouter_demo/models.py:1-48 existing; extended per CITED docs/specs/data-model.md]

class Status(StrEnum):
    PENDING = "pending"
    STREAMING = "streaming"
    SUCCEEDED = "succeeded"
    FALLBACK_SUCCEEDED = "fallback_succeeded"  # NEW
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass(frozen=True)
class AttemptRecord:
    """One attempt within a fallback scenario."""
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
    """Preserves both primary failure and fallback success evidence."""
    primary: AttemptRecord
    fallback: AttemptRecord
    simulated: bool

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
    fallback_evidence: FallbackEvidence | None  # NEW — None for normal runs
```

### Fallback Scenario Function

```python
# Source: [ASSUMED — new implementation following VERIFIED existing patterns from src/openrouter_demo/client.py and tests/test_ui.py]

import time
from collections.abc import AsyncIterator

from openrouter_demo.client import OpenRouterError, stream_chat_completion
from openrouter_demo.models import (
    AttemptRecord, FallbackEvidence, Status, StreamChunk, StreamedResult, UNAVAILABLE,
)
from openrouter_demo.routing import FALLBACK_PRIMARY_STRATEGY, RoutingStrategy

@dataclass(frozen=True)
class FallbackResult:
    primary: AttemptRecord
    fallback: StreamedResult | None
    simulated: bool

async def run_fallback_scenario(
    prompt: str,
    *,
    fallback_strategy: RoutingStrategy,
    api_key: str,
    stream_fn: Callable[..., AsyncIterator[StreamChunk | StreamedResult]] = stream_chat_completion,
) -> AsyncIterator[StreamChunk | FallbackResult]:
    # Primary attempt — deterministic failure
    primary_start = time.monotonic()
    primary_error: OpenRouterError | None = None
    try:
        async for _ in stream_fn(prompt, strategy=FALLBACK_PRIMARY_STRATEGY, api_key=api_key):
            pass
    except OpenRouterError as exc:
        primary_error = exc
    primary_latency_ms = int((time.monotonic() - primary_start) * 1000)

    primary_record = AttemptRecord(
        model=FALLBACK_PRIMARY_STRATEGY.model,
        provider=UNAVAILABLE,
        status=Status.FAILED,
        error_message=str(primary_error) if primary_error else "Primary unexpectedly succeeded",
        latency_ms=primary_latency_ms,
        prompt_tokens=UNAVAILABLE,
        completion_tokens=UNAVAILABLE,
        total_tokens=UNAVAILABLE,
        cost_usd=UNAVAILABLE,
    )

    # Fallback attempt — real strategy, stream chunks to UI
    fallback_result: StreamedResult | None = None
    async for event in stream_fn(prompt, strategy=fallback_strategy, api_key=api_key):
        if isinstance(event, StreamChunk):
            yield event
        elif isinstance(event, StreamedResult):
            fallback_result = event

    yield FallbackResult(primary=primary_record, fallback=fallback_result, simulated=True)
```

### UI Strategy Selector and Fallback Toggle

```python
# Source: [ASSUMED — new UI code following VERIFIED existing NiceGUI patterns from src/openrouter_demo/ui.py]

# Strategy selector replaces hardcoded "Default" label:
# [VERIFIED: src/openrouter_demo/ui.py:280-283 — current hardcoded DEFAULT_STRATEGY]
strategy_select = ui.select(
    options={s.name: ROUTING_STRATEGY_LABELS[s.name] for s in STRATEGIES.values()},
    value=DEFAULT_STRATEGY.name,
    on_change=lambda e: update_strategy_description(e.value),
)

# Strategy description updates on selection:
strategy_description_label = ui.label(DEFAULT_STRATEGY.description)

def update_strategy_description(strategy_name: str) -> None:
    strategy = STRATEGIES.get(strategy_name, DEFAULT_STRATEGY)
    strategy_description_label.text = strategy.description

# Fallback toggle:
simulate_failure = ui.switch("Simulate primary route failure", value=False)
ui.label("For a reproducible demo. The UI will label this as simulated.").classes("text-sm text-gray-600")

# In run_request(), read the selected strategy:
selected_strategy = STRATEGIES.get(strategy_select.value, DEFAULT_STRATEGY)
if simulate_failure.value:
    run = await _run_fallback_inference(prompt_text, strategy=selected_strategy, ...)
else:
    run = await _run_inference(prompt_text, strategy=selected_strategy, ...)
```

### Telemetry Rows for Fallback

```python
# Source: [CITED: docs/ux/screen-spec.md:208-211 — "Completed via fallback route after primary route failed."]

FALLBACK_SUCCESS_RESPONSE = "Completed via fallback route after primary route failed."
SIMULATED_FAILURE_LABEL = "Simulated failure triggered for demo."

def _telemetry_rows_with_fallback(run: InferenceRun) -> list[tuple[str, str]]:
    rows = _telemetry_rows(run)  # existing rows
    if run.fallback_evidence is not None:
        fe = run.fallback_evidence
        rows.append(("Primary status", fe.primary.status.value))
        rows.append(("Primary error", fe.primary.error_message or _UNAVAILABLE_COPY))
        rows.append(("Fallback model", _format_metadata(fe.fallback.model)))
        rows.append(("Fallback status", fe.fallback.status.value))
        if fe.simulated:
            rows.append(("Failure type", SIMULATED_FAILURE_LABEL))
    return rows
```

### OpenRouter Provider Routing Request Body (Verified)

```python
# Source: [VERIFIED: openrouter.ai/docs/guides/routing/provider-selection — Python requests examples]

# Default strategy — no provider key, OpenRouter load-balances by price:
{
    "model": "openai/gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": True
}

# Cost strategy — sort by price:
{
    "model": "openai/gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": True,
    "provider": {"sort": "price"}
}

# Latency strategy — sort by latency:
{
    "model": "openai/gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": True,
    "provider": {"sort": "latency"}
}

# Fallback primary — nonexistent model, no fallbacks (deterministic failure):
{
    "model": "nonexistent/fake-model-for-demo",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": True,
    "provider": {"allow_fallbacks": False}
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `model` field only (single model) | `models` array for server-side model fallback | Current OpenRouter docs | Enables automatic failover, but hides primary failure from client. Not suitable for demo evidence requirement. |
| No `provider` object | `provider` object with `sort`, `allow_fallbacks`, `order`, etc. | Current OpenRouter docs | Enables explicit routing preferences. Phase 3 uses `sort` for cost/latency strategies. |
| `sort` as string only | `sort` as string or object with `by` and `partition` | Current OpenRouter docs | `partition: "none"` enables cross-model sorting. Not needed for Phase 3 single-model strategies. |

**Deprecated/outdated:**
- None identified. The OpenRouter API parameters used in Phase 3 are current as of the verified docs fetch on 2026-08-19.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `model: "nonexistent/fake-model-for-demo"` with `allow_fallbacks: false` will deterministically return a 404 or error from OpenRouter. | Fallback Scenario Design, Code Examples | If OpenRouter accepts unknown model slugs, the primary won't fail. Mitigation: handle the edge case where primary unexpectedly succeeds. Manual smoke test needed. |
| A2 | The failed primary attempt costs zero tokens (no completion generated). | Common Pitfalls 6 | If OpenRouter charges for failed requests, fallback demo costs double. Mitigation: verify during manual smoke test. OpenRouter docs say "Requests are priced using the model that was ultimately used" — a failed request with no model used should be free. [CITED: openrouter.ai/docs/guides/routing/model-fallbacks] |
| A3 | NiceGUI `ui.select` supports dict options with value-label mapping and `on_change` callback. | UI Code Examples | If the API differs, the strategy selector implementation needs adjustment. Mitigation: check NiceGUI docs during execution. [ASSUMED — based on training knowledge of NiceGUI API] |
| A4 | The existing `stream_chat_completion` function can be reused for the fallback primary attempt without modification. | Fallback Scenario Design | The function already accepts `strategy` parameter and builds the body from `strategy_payload()`. If `strategy_payload()` is updated to include `provider`, the primary attempt will send `allow_fallbacks: false`. [VERIFIED: src/openrouter_demo/client.py:83-92 — body construction from strategy_payload] |
| A5 | `ui.switch` is the correct NiceGUI component for the fallback toggle. | UI Code Examples | If NiceGUI uses a different component name, the toggle implementation needs adjustment. [ASSUMED — based on training knowledge] |

## Open Questions

1. **Will the nonexistent model slug produce a 404 or a different error?**
   - What we know: OpenRouter returns errors for unknown models. The `OpenRouterHTTPError` class captures status codes. [VERIFIED: src/openrouter_demo/client.py:19-30]
   - What's unclear: The exact status code and error message format for a nonexistent model with `allow_fallbacks: false`.
   - Recommendation: Handle any `OpenRouterError` subclass as primary failure evidence. The specific error message is captured in `AttemptRecord.error_message` regardless of status code. Manual smoke test will reveal the exact error.

2. **Should the strategy selector be a dropdown or radio buttons?**
   - What we know: The screen spec says "Strategy selector" without specifying the control type. The UI/UX plan shows "Default / Cost / Latency" suggesting discrete options.
   - What's unclear: Whether NiceGUI's `ui.select` (dropdown) or `ui.radio` (radio buttons) is more appropriate for 3-4 options.
   - Recommendation: Use `ui.select` (dropdown) — it's more compact and scales if custom strategy is added later. The existing Phase 2 UI uses buttons for sample prompts, but a strategy selector is a single-value control, not a multi-button action.

3. **Should the "Custom" strategy from the screen spec be implemented in Phase 3?**
   - What we know: The screen spec defines four strategy options: Default, Cost optimized, Latency optimized, and Custom. ROUTE-01 requires "at least default, cost-oriented, and latency-oriented." `ROUTING_STRATEGY_LABELS` already includes "custom". [VERIFIED: src/openrouter_demo/routing.py:6-11, tests/test_imports.py:46-51]
   - What's unclear: Whether Custom needs a UI control in Phase 3 or just the label/type seam.
   - Recommendation: Do NOT add a Custom strategy UI control in Phase 3. ROUTE-01 only requires three strategies. The "custom" label exists in the type system for the `FALLBACK_PRIMARY_STRATEGY` (which uses `name="custom"`). A user-facing Custom strategy with explicit model/provider input is a potential Phase 4+ enhancement. Add it to the deferred list.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12+ | All code | ✓ | 3.12+ | — |
| uv | Dependency management | ✓ | existing | — |
| NiceGUI | UI | ✓ | ≥3.16.0 | — |
| httpx | OpenRouter HTTP | ✓ | ≥0.28.1 | — |
| pytest | Tests | ✓ | ≥9.1.1 | — |
| Ruff | Linting | ✓ | ≥0.16.3 | — |
| OPENROUTER_API_KEY | Live fallback demo | ✓ (configurable) | — | Tests use injected streams — no key needed for automated tests |

**Missing dependencies with no fallback:** none
**Missing dependencies with fallback:** none — all tests use injected async streams or `httpx.MockTransport`, no live API key required for automated coverage.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest ≥9.1.1 [VERIFIED: pyproject.toml:14] |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` [VERIFIED: pyproject.toml:21-23] |
| Quick run command | `uv run pytest tests/test_routing.py tests/test_scenarios.py tests/test_ui.py -x -q` |
| Full suite command | `uv run pytest && uv run ruff check .` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ROUTE-01 | Three strategies selectable, each produces correct provider params | unit | `uv run pytest tests/test_routing.py -x -q` | ❌ Wave 0 |
| ROUTE-02 | Strategy description text is reviewer-facing tradeoff language | unit | `uv run pytest tests/test_routing.py::test_strategy_descriptions -x` | ❌ Wave 0 |
| ROUTE-03 | Completed run shows selected strategy + actual model/provider evidence | unit | `uv run pytest tests/test_ui.py::test_run_inference_with_selected_strategy -x` | ❌ Wave 0 (extend existing) |
| ROUTE-04 | Fallback scenario can be triggered via toggle | unit | `uv run pytest tests/test_scenarios.py::test_fallback_scenario_primary_fails -x` | ❌ Wave 0 |
| ROUTE-05 | Fallback evidence shows primary attempt, failure reason, fallback route, final result | unit | `uv run pytest tests/test_scenarios.py::test_fallback_evidence_preserves_both_attempts -x` | ❌ Wave 0 |
| ROUTE-06 | Successful fallback does not hide primary failure evidence | unit | `uv run pytest tests/test_ui.py::test_fallback_success_shows_primary_failure -x` | ❌ Wave 0 (extend existing) |

### Test Dimensions

| Dimension | Coverage Target | Verification Approach |
|-----------|----------------|----------------------|
| Strategy payloads | Each strategy (default, cost, latency, fallback_primary) emits correct `provider` params | Unit test: assert `strategy_payload(COST_STRATEGY)["provider"] == {"sort": "price"}` |
| Strategy descriptions | Each strategy has non-empty description matching screen spec copy | Unit test: assert descriptions match exact strings from `docs/ux/screen-spec.md` |
| Fallback scenario — primary failure | Primary attempt with nonexistent model fails with `OpenRouterError` | Unit test with injected failing stream: assert `primary_record.status == Status.FAILED` |
| Fallback scenario — fallback success | Fallback attempt yields `StreamedResult` with real model/provider | Unit test with injected success stream: assert `fallback_result.model == "openai/gpt-4o-mini"` |
| Fallback evidence preservation | Both `AttemptRecord` objects present on `InferenceRun.fallback_evidence` | Unit test: assert `run.fallback_evidence.primary.status == FAILED` and `run.fallback_evidence.fallback.status == SUCCEEDED` |
| Fallback status distinction | `Status.FALLBACK_SUCCEEDED` ≠ `Status.SUCCEEDED` | Unit test: assert `run.status is Status.FALLBACK_SUCCEEDED` |
| Metadata honesty in fallback | Primary attempt's tokens/cost are `UNAVAILABLE`, not zero | Unit test: assert `primary_record.cost_usd is UNAVAILABLE` and `primary_record.prompt_tokens is UNAVAILABLE` |
| UI strategy selector | Selecting a strategy updates the description and passes the strategy to the run handler | Unit test with injected stream: assert `run.strategy_name == "cost"` when cost selected |
| UI fallback toggle | Toggle on routes through fallback scenario; toggle off routes through normal stream | Unit test: assert `run.status is Status.FALLBACK_SUCCEEDED` when toggle on, `Status.SUCCEEDED` when off |
| UI fallback rendering | Fallback run renders primary failure details and fallback success copy | Unit test: assert `_telemetry_rows(run)` includes "Primary status" and fallback response copy |
| History with fallback | Run history includes fallback column | Unit test: assert `_history_rows(history)` includes fallback indicator |
| Simulated label | Fallback evidence marked as simulated when toggle is used | Unit test: assert `run.fallback_evidence.simulated is True` |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_routing.py tests/test_scenarios.py tests/test_ui.py -x -q`
- **Per wave merge:** `uv run pytest && uv run ruff check .`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_routing.py` — covers REQ ROUTE-01, ROUTE-02 (strategy payloads and descriptions)
- [ ] `tests/test_scenarios.py` — covers REQ ROUTE-04, ROUTE-05 (fallback scenario orchestration and evidence)
- [ ] `tests/test_ui.py` (extend) — covers REQ ROUTE-03, ROUTE-06 (strategy selector, fallback toggle, fallback rendering)
- [ ] `tests/test_imports.py` (extend) — verify new types (`AttemptRecord`, `FallbackEvidence`, `Status.FALLBACK_SUCCEEDED`) import; update scenario stub expectation (scenarios no longer raises `PhaseNotImplementedError` for fallback)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | OpenRouter API key via env var (existing Phase 1 pattern) |
| V3 Session Management | no | No sessions — local demo app |
| V4 Access Control | no | No multi-user access — local demo |
| V5 Input Validation | yes | Prompt non-empty validation (existing); strategy name validated against `STRATEGIES` dict; fallback toggle is boolean |
| V6 Cryptography | no | No crypto operations in this phase |

### Known Threat Patterns for Python/NiceGUI Local Demo

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| API key exposure in request body | Information Disclosure | Key sent via `Authorization` header only, never in body or URL. [VERIFIED: src/openrouter_demo/client.py:73-75] |
| Injection via prompt text | Injection | Prompt is sent as user message content to OpenRouter, not executed locally. No SQL/command injection surface (no database, no shell). |
| Nonexistent model in fallback | Denial of Service | The nonexistent model is a hardcoded constant in `FALLBACK_PRIMARY_STRATEGY`, not user-supplied. Users cannot inject arbitrary model names. |

## Project Constraints (from AGENTS.md / copilot-instructions.md)

| Constraint | Source | How Phase 3 Complies |
|------------|--------|---------------------|
| Python 3.12+, NiceGUI, httpx, uv, Ruff, pytest | AGENTS.md Tech stack | No new packages; uses existing stack exclusively |
| Direct OpenRouter HTTPS calls (no SDK hiding routing metadata) | AGENTS.md OpenRouter integration | `strategy_payload()` emits `provider` object directly in request body; `stream_chat_completion` sends it via httpx |
| Langfuse optional (missing credentials must not block) | AGENTS.md Observability | No Langfuse changes in Phase 3; tracing remains Phase 4 scope |
| Metadata honesty: UNAVAILABLE distinct from zero | AGENTS.md Metadata honesty | `AttemptRecord` for failed primary uses `UNAVAILABLE` sentinels for tokens/cost/provider; format helpers render honest copy |
| Cost bounded: small prompts, cheap eval cases | AGENTS.md Cost | Fallback primary costs zero (failed 404, no tokens); fallback uses same `openai/gpt-4o-mini` as default |
| Single-screen UI (no navigation) | AGENTS.md UI scope | Strategy selector and fallback toggle added to existing single screen |
| No database, no background queue, no separate frontend | AGENTS.md Out of scope | Run history stays in-memory; no new persistence layers |
| UI avoids chatbot framing | docs/specs/acceptance-criteria.md | Strategy panel and fallback controls reinforce inference operations console metaphor |
| `scenarios.py` owns deterministic demo scenarios | docs/specs/acceptance-criteria.md | Fallback scenario implementation lives in `scenarios.py` |
| `routing.py` owns model/provider strategy definitions | docs/specs/acceptance-criteria.md | New strategy instances and `strategy_payload()` update live in `routing.py` |
| UI code does not embed business/inference logic | docs/specs/acceptance-criteria.md | UI reads strategy descriptions and passes strategy objects to stream/scenario functions; no routing logic in UI |

## Sources

### Primary (HIGH confidence)

- **OpenRouter Provider Routing** — https://openrouter.ai/docs/guides/routing/provider-selection
  - Fetched via Context7 `/websites/openrouter_ai` and direct webpage fetch on 2026-08-19
  - Verified: `provider` object fields (`order`, `allow_fallbacks`, `sort`, `only`, `ignore`, `preferred_max_latency`, `preferred_min_throughput`, `max_price`, `require_parameters`, `data_collection`, `quantizations`, `zdr`, `enforce_distillable_text`)
  - Verified: `sort` accepts string (`"price"`, `"throughput"`, `"latency"`) or object (`{by, partition}`)
  - Verified: Default behavior is price-based load balancing with fallbacks enabled
  - Verified: `allow_fallbacks: false` disables provider fallback
  - Verified: Python `requests` examples use snake_case (`allow_fallbacks`, `preferred_max_latency`)

- **OpenRouter Model Fallbacks** — https://openrouter.ai/docs/guides/routing/model-fallbacks
  - Fetched via Context7 and direct webpage fetch on 2026-08-19
  - Verified: `models` array field enables server-side model fallback
  - Verified: Server-side fallback is invisible to client — no primary failure event exposed
  - Verified: "Requests are priced using the model that was ultimately used" (failed primary = free)
  - Verified: Fallback triggers on context length errors, moderation flags, rate-limiting, downtime

- **Existing source code** — Read this session:
  - `src/openrouter_demo/routing.py` (lines 1-34): `StrategyName`, `ROUTING_STRATEGY_LABELS`, `RoutingStrategy`, `DEFAULT_STRATEGY`, `strategy_payload()`
  - `src/openrouter_demo/client.py` (lines 1-145): `stream_chat_completion`, error types, SSE parsing, metadata extraction
  - `src/openrouter_demo/models.py` (lines 1-48): `Unavailable`, `UNAVAILABLE`, `Status`, `StreamChunk`, `StreamedResult`, `TelemetryEvidence`, `InferenceRun`
  - `src/openrouter_demo/ui.py` (lines 1-310): `_run_inference`, `_telemetry_rows`, `_history_rows`, `build_app`, formatting helpers
  - `src/openrouter_demo/scenarios.py` (lines 1-5): `PhaseNotImplementedError`, `run_scenario` stub
  - `src/openrouter_demo/history.py` (lines 1-14): `RunHistory`
  - `src/openrouter_demo/config.py` (lines 1-40): `AppConfig`, `load_config`
  - `tests/test_client.py` (lines 1-155): SSE test patterns, `httpx.MockTransport`, metadata extraction tests
  - `tests/test_ui.py` (lines 1-155): Injected async stream tests, telemetry row tests, history row tests
  - `tests/test_imports.py` (lines 1-60): Module import guards, `ROUTING_STRATEGY_LABELS` exact equality test
  - `tests/test_phase1_guards.py` (lines 1-20): No FastAPI, no database, no Langfuse trace creation

### Secondary (MEDIUM confidence)

- `docs/ux/screen-spec.md` — Strategy panel spec, fallback success copy, telemetry fields, error patterns
- `docs/ux/ui-ux-plan.md` — Main screen structure, strategy panel controls, response panel states
- `docs/ux/demo-narrative.md` — Five-minute walkthrough flow for routing and fallback sections
- `docs/specs/data-model.md` — `FallbackAttempt` entity spec, `RoutingStrategy` fields, `TelemetryEvidence` fields
- `docs/specs/acceptance-criteria.md` — Demo-critical, UI/UX, and repository acceptance criteria
- `docs/specs/failure-tree.md` — OpenRouter routing failure branches
- `docs/design/DESIGN-light.md` — Vibrant Kinetic design system (colors, typography, spacing, components)
- `.planning/research/PITFALLS.md` — Pitfall 2: Silent or Hidden Fallback
- `.planning/phases/02-streaming-inference-evidence/02-RESEARCH.md` — Phase 2 patterns and OpenRouter facts
- `.planning/phases/02-streaming-inference-evidence/02-UI-SPEC.md` — Layout contract and required copy

### Tertiary (LOW confidence)

- NiceGUI `ui.select` and `ui.switch` API details — [ASSUMED] based on training knowledge, not verified via Context7 this session. Verify during execution.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages, all existing from Phase 1/2
- OpenRouter API: HIGH — verified via Context7 and direct webpage fetch on 2026-08-19
- Architecture: HIGH — follows existing Phase 2 patterns, clear data model from `docs/specs/data-model.md`
- Fallback scenario design: HIGH — client-side two-attempt approach is well-reasoned; one assumption (A1: nonexistent model deterministically fails) needs manual smoke test
- Pitfalls: HIGH — grounded in existing code, tests, and domain pitfalls doc
- NiceGUI UI components: MEDIUM — component API not verified via docs this session

**Research date:** 2026-08-19
**Valid until:** 2026-09-19 (30 days — OpenRouter API is stable; no fast-moving dependencies)