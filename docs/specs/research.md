# Research: OpenRouter Inference Lab

## Decision: Use direct OpenRouter Chat Completions requests over HTTPS

**Rationale**: OpenRouter's Chat Completions endpoint supports streaming responses and a
`provider` object for routing preferences, fallback control, latency preferences, price
sorting, provider allow/deny lists, and cache-related options. Direct requests keep the demo
focused on OpenRouter behavior instead of hiding it behind another router or SDK.

**Alternatives considered**:
- OpenAI-compatible SDK: convenient, but can obscure OpenRouter-specific provider routing,
  fallback, metadata, and cache fields during an interview walkthrough.
- Unofficial OpenRouter client: unnecessary surface area for a small demo.
- Another inference router: rejected by constitution; OpenRouter must own the routing story.

## Decision: Use a small async HTTP helper for OpenRouter calls

**Rationale**: The UI needs streaming updates and explicit timeout/error handling. A small
HTTP client wrapper around OpenRouter's endpoint is easier to inspect than a larger SDK and
keeps request bodies visible. The wrapper owns only request construction, streaming event
parsing, timeout handling, and response metadata normalization.

**Alternatives considered**:
- Standard-library HTTP only: fewer dependencies, but more code for async streaming and
  timeout behavior.
- Full OpenAI SDK: less custom code for streaming, but more indirection around
  OpenRouter-specific request body and metadata handling.

## Decision: Use NiceGUI as a local browser UI only

**Rationale**: NiceGUI provides Python-native labels, inputs, selectors, buttons, timers, and
async event handlers, which are sufficient for prompt entry, strategy selection, streaming
response updates, telemetry cards, trace links, and eval results. The demo does not need a
separate frontend project or a separate API service.

**Alternatives considered**:
- CLI only: simpler, but weaker for the five-minute interview demo because runtime evidence
  is less visible.
- Separate JavaScript frontend: rejected by constitution and PRD non-goals.
- Separate FastAPI service: rejected; NiceGUI's internal framework is an implementation
  detail, not an architecture layer.

## Decision: Use Langfuse as optional tracing/eval observability

**Rationale**: Langfuse's Python SDK supports spans/generations, usage details, cost details,
scores, and flush. Tracing can be enabled only when credentials exist; otherwise the app
should expose tracing as disabled while preserving core inference runs.

**Alternatives considered**:
- Required Langfuse credentials: rejected because the core demo must run with only the
  OpenRouter credential.
- Local-only logs: useful fallback, but insufficient for the promised Langfuse-traced evals.

## Decision: Use deterministic eval scoring as the floor

**Rationale**: Deterministic checks over three to five cases keep evals cheap, repeatable,
and inspectable. They satisfy the demo's evidence requirement before any optional
LLM-as-judge scoring is added.

**Alternatives considered**:
- LLM-as-judge first: more impressive but adds cost, variability, and another dependency path.
- Full eval harness: rejected by scope; the project is an interview demo, not a platform.

## Decision: Use environment variables and `.env.example` for configuration

**Rationale**: `OPENROUTER_API_KEY` is required. Langfuse variables are optional. The demo
must never commit secrets and must make missing credential behavior explicit.

**Alternatives considered**:
- Config files containing credentials: rejected for secret-safety reasons.
- Interactive credential entry only: inconvenient for repeated reviewer runs and harder to
  document in quickstart.

## Decision: Keep persistence in files only where useful for examples

**Rationale**: The specification explicitly excludes databases and background queues. Eval
cases can live in `evals/cases.json`; runtime results can stay in memory for the local demo
and be visible in the UI/Langfuse.

**Alternatives considered**:
- Database persistence: rejected by scope and constitution.
- Background job queue: rejected; eval set is intentionally small.

## Decision: Use uv, Ruff, and pytest as quality gates

**Rationale**: The PRD and constitution require uv for dependency/command execution, Ruff for
lint/format, and focused pytest coverage for response/error handling, routing configuration,
and eval scoring.

**Alternatives considered**:
- Make-only workflow: acceptable as a wrapper, but uv remains canonical.
- Broad test suite first: unnecessary for an interview demo; focused tests cover the core
  failure-prone logic.
