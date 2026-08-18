# Implementation Plan: OpenRouter Inference Lab

**Branch**: `001-openrouter-inference-lab` | **Date**: 2026-08-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-openrouter-inference-lab/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Build a compact local OpenRouter inference lab for interview use. The app runs live
streaming inference, exposes routing/fallback/cost/latency/cache-or-repeat evidence,
optionally links runs to Langfuse, and runs a three-to-five-case deterministic eval set. The
implementation stays Python-first: NiceGUI for the local browser UI, a small direct
OpenRouter client wrapper for streaming/error/metadata behavior, simple dataclass-style
models for telemetry, and focused pytest coverage for the risky logic.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: NiceGUI, Langfuse Python SDK, httpx as the small async HTTP helper,
pytest, Ruff

**Storage**: Files only for checked-in eval cases (`evals/cases.json`); runtime results stay
in memory and Langfuse when configured

**Testing**: pytest for response/error handling, routing configuration, telemetry
normalization, and eval scoring; Ruff for lint/format

**Target Platform**: Local developer machine running a browser-accessible NiceGUI app

**Project Type**: Single Python local web app / interview demo

**Performance Goals**: Reviewer can run setup in <=10 minutes; candidate can complete the
core demo sequence in <=5 minutes after setup; streaming UI updates progressively during a
live run

**Constraints**: Direct OpenRouter integration; no separate frontend, API service, database,
auth, multi-tenancy, queue, or required Docker path; Langfuse optional; no invented metadata;
bounded low-cost default workloads

**Scale/Scope**: One local user, four demo scenarios, three routing strategies, one
reproducible fallback path, three-to-five eval cases

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Gate

- Demonstrates OpenRouter value: PASS — streaming, routing, fallback, cache/repeat,
  cost/latency comparison, evals, and observability are the explicit feature scope.
- Direct Python/OpenRouter path preserved: PASS — direct OpenRouter Chat Completions over
  HTTPS from Python; NiceGUI is only the local UI.
- Observability and eval evidence planned: PASS — Langfuse tracing is optional but visible;
  deterministic eval scoring is required.
- Reliability, secrets, and cost controls planned: PASS — visible failure/fallback states,
  env-var credentials, `.env.example`, and bounded default workloads are required.
- Small testable surface: PASS — single Python package, no production SaaS layers, focused
  pytest/Ruff/uv validation.

### Post-Design Gate

- Demonstrates OpenRouter value: PASS — data model and contracts center on inference runs,
  routing strategies, fallback attempts, telemetry evidence, and eval results.
- Direct Python/OpenRouter path preserved: PASS — contracts expose local UI/command behavior
  only; no public product API or separate service is introduced.
- Observability and eval evidence planned: PASS — telemetry fields, trace status, and eval
  score records are modeled and validated.
- Reliability, secrets, and cost controls planned: PASS — quickstart covers missing
  credentials, optional tracing, fallback, repeat/cache uncertainty, and cheap demo runs.
- Small testable surface: PASS — files match the PRD layout and avoid speculative modules.

## Project Structure

### Documentation (this feature)

```text
specs/001-openrouter-inference-lab/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── local-demo-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
README.md
Makefile
pyproject.toml
uv.lock
.env.example
app.py

src/
└── openrouter_demo/
    ├── __init__.py
    ├── client.py
    ├── config.py
    ├── evals.py
    ├── models.py
    ├── routing.py
    ├── scenarios.py
    ├── telemetry.py
    └── ui.py

evals/
└── cases.json

docs/
├── architecture.md
└── failure-tree.md

tests/
├── test_response_handling.py
├── test_routing_config.py
└── test_eval_scoring.py
```

**Structure Decision**: Use the PRD's single-package Python layout. It is the smallest layout
that separates UI from inference logic while keeping code inspectable during a walkthrough.
No backend/frontend split, database layer, or queue is planned.

## Complexity Tracking

No constitution violations. No added complexity requires justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
