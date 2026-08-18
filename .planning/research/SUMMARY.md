# Research Summary: OpenRouter Production Inference Lab

**Domain:** Local production-inference interview demo
**Researched:** 2026-08-18
**Overall confidence:** HIGH

## Executive Summary

The existing seed docs describe a coherent v1: a compact Python-first demo that makes OpenRouter production behavior visible. Current official docs support the core premise: OpenRouter Chat Completions supports streaming, provider routing preferences, fallback controls, usage data, cache controls, and opt-in router metadata.

NiceGUI remains a good fit for the local UI because it supports Python-defined browser interfaces, async event handlers, background tasks, Tailwind utility classes, and `ui.run()` without a separate frontend project. The implementation should avoid blocking the UI event loop while streaming OpenRouter responses.

Langfuse should stay optional. Current Langfuse Python SDK docs support generation/span tracing, `usage_details`, `cost_details`, scoring, and flushing, which maps well to inference runs and eval results. Missing Langfuse credentials should produce a visible "tracing disabled" state, not a failed demo.

The biggest implementation risk is not API feasibility; it is credibility. The demo must distinguish unavailable metadata from zeros, preserve failed primary attempts when fallback succeeds, and avoid unsupported cache claims.

## Key Findings

**Stack:** Python 3.12+, NiceGUI, httpx, direct OpenRouter HTTPS calls, optional Langfuse Python SDK, uv, Ruff, and pytest.

**Architecture:** Single Python package with strict internal boundaries for client, routing, scenarios, telemetry, evals, and UI.

**Critical pitfall:** Do not invent metadata. Missing token, cost, provider, router, and cache details must render as unavailable.

## Implications for Roadmap

Suggested vertical phase structure:

1. **Runnable Skeleton and Config** - establish `uv` project, env handling, app entrypoint, package layout, and setup docs.
   - Addresses: setup, secrets, run path.
   - Avoids: fragile reviewer setup.

2. **Streaming Inference Evidence** - ship the first live OpenRouter streaming call with progressive UI updates and basic telemetry.
   - Addresses: core demo proof.
   - Avoids: static or non-progressive demo.

3. **Routing and Fallback Demo** - add cost/latency/default strategies and reproducible fallback with preserved failure evidence.
   - Addresses: production reliability and routing tradeoffs.
   - Avoids: silent fallback.

4. **Telemetry, Repeat/Cache, and Observability** - enrich metadata display, cache/repeat honesty, run history, and optional Langfuse traces.
   - Addresses: cost/latency/cache/trace evidence.
   - Avoids: fabricated metadata or required tracing.

5. **Deterministic Evals and Walkthrough** - add eval cases, scoring, trace scores when enabled, README, architecture doc, and failure tree.
   - Addresses: evidence-based model selection and interview narrative.
   - Avoids: subjective quality claims.

6. **Quality Gates and Demo Polish** - add focused tests, Ruff checks, UI polish, and verify quickstart commands.
   - Addresses: engineering discipline and final demo readiness.
   - Avoids: walkthrough/code drift.

**Phase ordering rationale:** each phase produces an end-to-end demonstrable improvement while preserving the ability to run the demo after Phase 1.

**Research flags for phases:**

- Phase 2: Confirm final OpenRouter streaming chunk and usage handling during implementation.
- Phase 3: Confirm exact provider strategy request bodies against OpenRouter docs and real responses.
- Phase 4: Confirm Langfuse SDK method names against installed package version after dependency lock.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Confirmed against seed docs, official OpenRouter docs, Context7 NiceGUI docs, Context7 Langfuse docs, and Context7 uv docs. |
| Features | HIGH | Existing acceptance criteria are detailed and align with current API capabilities. |
| Architecture | HIGH | The single-package Python layout matches project constraints and avoids unnecessary layers. |
| Pitfalls | HIGH | Main risks are explicit in seed docs and current OpenRouter/NiceGUI/Langfuse behavior. |

## Gaps to Address

- Exact model slugs and provider constraints should be chosen during implementation using current OpenRouter model availability.
- Cache metadata behavior must be verified with actual responses; v1 should be ready to show repeat observations when cache metadata is absent.
- Langfuse API shape should be pinned by the installed package version in `uv.lock`.

## Sources

- `docs/PRD.md`
- `docs/specs/acceptance-criteria.md`
- `docs/specs/data-model.md`
- `docs/specs/quickstart.md`
- OpenRouter Quickstart: https://openrouter.ai/docs/quickstart
- OpenRouter Chat Completions API: https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request
- OpenRouter Streaming: https://openrouter.ai/docs/api/reference/streaming
- OpenRouter Provider Routing: https://openrouter.ai/docs/guides/routing/provider-selection
- OpenRouter Router Metadata: https://openrouter.ai/docs/guides/features/router-metadata
- NiceGUI docs via Context7 `/zauberzeug/nicegui`
- Langfuse Python SDK docs via Context7 `/langfuse/langfuse-python`
- uv docs via Context7 `/astral-sh/uv`
- Ruff docs: https://docs.astral.sh/ruff/formatter/
- pytest docs: https://docs.pytest.org/en/stable/getting-started.html
