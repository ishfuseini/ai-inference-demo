# Feature Landscape

**Domain:** Local production-inference interview demo
**Researched:** 2026-08-18
**Overall confidence:** HIGH

## Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| One-command setup and run path | Interviewer must be able to run the demo quickly | Medium | `uv sync` and `uv run python app.py` are the canonical commands. |
| Streaming inference | The core proof is a live model call, not a static response | Medium | OpenRouter supports `stream: true`; final chunks can carry usage. |
| Visible telemetry | Routing/cost/latency claims need evidence | Medium | Display model, provider, latency, tokens, cost, fallback, cache/repeat, and trace state when available. |
| Multiple routing strategies | Cost and latency tradeoffs require comparable routes | Medium | OpenRouter provider sorting supports price, throughput, and latency preferences. |
| Reproducible fallback scenario | Reliability must be demonstrable on demand | Medium | The demo can use a clearly labeled deterministic failure trigger before a real fallback route. |
| Optional Langfuse tracing | Observability is promised but should not block core inference | Medium | Missing credentials should show tracing disabled. |
| Deterministic eval set | Model selection needs quality evidence | Medium | Three to five cases with pass/fail criteria are enough for v1. |
| Failure tree and walkthrough docs | The artifact must support interview discussion | Low | Existing seed docs already define the target docs. |
| Focused tests | Failure-prone logic must be defensible | Medium | Cover response/error handling, routing config, telemetry normalization, and eval scoring. |

## Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Router metadata display | Shows what OpenRouter actually routed and retried | Medium | Requires `X-OpenRouter-Metadata: enabled`; cache hits may omit metadata. |
| Cache/repeat honesty | Demonstrates production caution instead of overclaiming | Medium | Report cache metadata only when returned; otherwise report observed repeat latency/cost. |
| Side-by-side run history | Makes tradeoffs visible in the main screen | Medium | Keep in memory for the local session. |
| Langfuse eval scores | Connects quality evidence to traces | Medium | Langfuse SDK supports scoring spans/generations. |

## Anti-Features

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Authentication and users | Not needed for local interview demo | Use env vars and local runtime state. |
| Database persistence | Adds setup and architecture not needed for v1 | Store eval cases in files and run history in memory. |
| Separate API service | Dilutes the Python-first, inspectable artifact | Keep service logic inside the Python package and UI entrypoint. |
| Full eval platform | Too large for the interview proof | Ship deterministic evals first. |
| Guaranteed cache claims | Providers may omit cache metadata or behave differently by route | Label cache unavailable and show repeat observations. |

## Feature Dependencies

```text
Setup -> Streaming inference -> Telemetry -> Routing comparison
Streaming inference -> Fallback scenario -> Failure visibility
Streaming inference -> Repeat/cache scenario
Streaming inference + Telemetry -> Deterministic evals
All demo behavior -> README, walkthrough, failure tree
Core logic -> Focused tests and Ruff gate
```

## MVP Recommendation

Prioritize:
1. Runnable `uv` project and credential handling.
2. Live streaming OpenRouter call with honest metadata display.
3. Routing and fallback scenarios with visible primary/fallback evidence.
4. Optional Langfuse traces and deterministic eval comparison.
5. Walkthrough docs and focused quality gates.

Defer:

- LLM-as-judge evals - useful later, but deterministic scoring is the v1 floor.
- Docker - optional convenience, not the core path.
- Hosted deployment - outside the local interview scope.

## Sources

- `docs/PRD.md`
- `docs/specs/acceptance-criteria.md`
- `docs/specs/data-model.md`
- OpenRouter Provider Routing: https://openrouter.ai/docs/guides/routing/provider-selection
- OpenRouter Router Metadata: https://openrouter.ai/docs/guides/features/router-metadata
- Langfuse Python SDK docs via Context7 `/langfuse/langfuse-python`
