# OpenRouter Production Inference Lab

## What This Is

A self-contained Python demo repo for a Forward Deployed Engineer interview. It shows a live OpenRouter inference workflow with streaming responses, routing strategies, fallback behavior, cost and latency evidence, repeat/cache observations, deterministic evals, and optional Langfuse traces.

The product is not a SaaS app. It is an inspectable local lab that lets the candidate demonstrate how production inference behaves when model calls must be operated, debugged, compared, and explained.

## Core Value

Make production inference behavior visible and defensible in a five-minute interview demo.

## Requirements

### Validated

- [x] Reviewer can install and run the local demo with `uv`. Validated in Phase 01: Runnable Skeleton and Config. — v1.0
- [x] Candidate can run a real streaming OpenRouter request from a NiceGUI interface. Validated in Phase 02: Streaming Inference Evidence. — v1.0
- [x] Candidate can compare routing strategies using visible model, provider, latency, token, cost, fallback, and trace evidence. Validated in Phase 03: Routing and Fallback Demo. — v1.0
- [x] Candidate can trigger a reproducible fallback path that preserves the failed primary attempt and the recovery attempt. Validated in Phase 03: Routing and Fallback Demo. — v1.0
- [x] Candidate can report cache/repeat behavior honestly, without claiming cache hits unless metadata supports it. Validated in Phase 04: Telemetry, Repeat, and Observability. — v1.0
- [x] Candidate can run a small deterministic eval set across strategy/model choices. Validated in Phase 05: Deterministic Evals. — v1.0
- [x] Reviewer can inspect concise docs, failure tree, and focused tests during a technical walkthrough. Validated in Phase 06: Interview Walkthrough and Quality Gates. — v1.0

### Active

(None — all v1 requirements validated)

### Validated — v1.0

### Out of Scope

- Production SaaS features - authentication, multi-tenancy, billing, HA, and hosted deployment do not support the interview proof.
- Separate frontend or backend service - the demo stays Python-first with NiceGUI as the local UI.
- Database or background job queue - runtime state can remain in memory; checked-in eval cases live in files.
- Full eval platform or golden-set pipeline - v1 needs only deterministic, cheap, inspectable evals.
- Docker as the core path - useful later, but `uv` remains the canonical setup and run path.
- Invented telemetry - unavailable provider metadata must stay visibly unavailable.

## Context

Shipped v1.0 with 2,188 LOC Python source and 2,664 LOC tests across 104 commits over 3 days. Tech stack: Python 3.12+, NiceGUI, httpx, Langfuse Python SDK, uv, Ruff, pytest. All 39 requirements validated, 105 tests pass, ruff clean.

Seed context remains in `docs/` and `data/`. The main product source is `docs/PRD.md`, supported by UX specs, acceptance criteria, a data model, quickstart, failure tree, and design references.

The demo is aimed at two people:

- The interviewer, who needs to understand the artifact in about 30 seconds, see the core behavior in about five minutes, and inspect the implementation during a 15-minute discussion.
- The candidate, who needs a compact, honest proof that they can debug and reason about real inference routing, fallback, caching, cost, latency, evals, and observability.

The implemented product is a single Python package (`src/openrouter_demo/`) with a thin `app.py` entrypoint, NiceGUI UI code, a direct OpenRouter client, routing/scenario definitions, telemetry normalization, SQLite persistence, deterministic eval scoring, and 11 test modules.

## Constraints

- **Tech stack**: Python 3.12+, NiceGUI, httpx, Langfuse Python SDK, uv, Ruff, pytest - this keeps the project Python-first and interview-inspectable.
- **OpenRouter integration**: Use direct OpenRouter Chat Completions requests over HTTPS - the demo must not hide OpenRouter-specific routing or metadata behind another router.
- **Observability**: Langfuse is optional at runtime - missing Langfuse credentials must disable tracing visibly without blocking inference.
- **Secrets**: Use environment variables and `.env.example`; never commit API keys.
- **Cost**: Default prompts and eval cases must remain small and bounded.
- **Metadata honesty**: Token, cost, provider, router, and cache fields must distinguish unavailable values from zero values.
- **UI scope**: NiceGUI is the local browser UI; FastAPI is only an internal NiceGUI implementation detail.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use existing `docs/` and `data/` as seed material | The repo already contains PRD, UX, acceptance, research, and data artifacts for this exact demo | ✓ Good — seed docs grounded every phase; no rework needed |
| Use Vertical MVP roadmap mode | Each phase should produce an interview-demonstrable capability, not isolated layers that only work at the end | ✓ Good — every phase shipped a demoable slice; no "big bang" risk |
| Use direct OpenRouter HTTP calls | Keeps request bodies, streaming, provider routing, fallback, and metadata inspectable | ✓ Good — all OpenRouter-specific fields visible in UI and telemetry |
| Use NiceGUI for the UI | Preserves a Python-first repo while giving the interviewer visible runtime evidence | ✓ Good — streaming, telemetry, history, and comparison all rendered in one local app |
| Keep Langfuse optional | Core demo must run with only `OPENROUTER_API_KEY` | ✓ Good — `config.langfuse_ready` gate works; tracing never blocks inference |
| Use uv, Ruff, and pytest | Matches seed docs and provides a simple quality gate path | ✓ Good — 105 tests pass, ruff clean, single-command setup |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? Move to Out of Scope with reason.
2. Requirements validated? Move to Validated with phase reference.
3. New requirements emerged? Add to Active.
4. Decisions to log? Add to Key Decisions.
5. "What This Is" still accurate? Update if drifted.

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections.
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state.

---
*Last updated: 2026-08-20 after v1.0 milestone*
