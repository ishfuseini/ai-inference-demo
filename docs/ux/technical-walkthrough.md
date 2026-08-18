# Technical Walkthrough - OpenRouter Production Inference Lab

## Purpose

This document maps likely interview questions to the files and concepts that answer them. It exists so the code inspection portion of the demo feels intentional.

## Walkthrough principle

Open the smallest file that answers the question. Do not tour the repo. Show the implementation seam that proves the point.

## Recommended inspection order

1. `app.py` — app entry point
2. `src/openrouter_demo/ui.py` — screen composition only
3. `src/openrouter_demo/routing.py` — strategy definitions
4. `src/openrouter_demo/client.py` — OpenRouter streaming and response handling
5. `src/openrouter_demo/telemetry.py` — normalized metrics and traces
6. `src/openrouter_demo/scenarios.py` — deterministic demo scenarios
7. `src/openrouter_demo/evals.py` — eval cases and scoring

## If they ask: “Where does the OpenRouter call happen?”

Open:

```text
src/openrouter_demo/client.py
```

Explain:

- request construction
- OpenRouter-compatible chat completion payload
- streaming handling
- timeout/error handling
- response metadata extraction

Key point:

> OpenRouter is used directly. There is no second inference router hiding the behavior.

## If they ask: “How do routing strategies work?”

Open:

```text
src/openrouter_demo/routing.py
```

Explain:

- default strategy
- cost-oriented strategy
- latency-oriented strategy
- explicit model/provider preferences
- fallback route configuration

Key point:

> Strategies should be inspectable policy objects, not scattered conditionals in UI code.

## If they ask: “How does fallback work?”

Open:

```text
src/openrouter_demo/scenarios.py
src/openrouter_demo/client.py
src/openrouter_demo/routing.py
```

Explain:

- the reproducible failure trigger lives in scenario logic
- the route/fallback options live in routing config
- the client reports failure and fallback attempts visibly

Key point:

> Fallback should not erase the failed attempt. The operator needs to know that fallback happened and why.

## If they ask: “Where is telemetry normalized?”

Open:

```text
src/openrouter_demo/telemetry.py
src/openrouter_demo/models.py
```

Explain:

- latency timing
- token/cost metadata normalization
- cache/repeat metadata where available
- fallback status
- Langfuse trace identifiers
- disabled tracing behavior

Key point:

> Missing metadata is a real production condition. The app should distinguish unknown/unavailable from zero.

## If they ask: “What happens without Langfuse credentials?”

Open:

```text
src/openrouter_demo/config.py
src/openrouter_demo/telemetry.py
```

Explain:

- OpenRouter key is required for live inference
- Langfuse keys are optional
- tracing should degrade gracefully
- UI should say tracing is disabled

Key point:

> Observability should improve the demo, not make the demo impossible to run.

## If they ask: “How do evals work?”

Open:

```text
src/openrouter_demo/evals.py
evals/cases.json
```

Explain:

- small deterministic eval set
- clear pass/fail rule per case
- result includes quality, latency, cost, route/model, trace
- optional LLM-as-judge is polish, not the core requirement

Key point:

> Evals are here to prove the decision loop, not to become a benchmark platform.

## If they ask: “Why not a separate frontend?”

Open:

```text
src/openrouter_demo/ui.py
```

Explain:

- NiceGUI keeps it Python-first
- UI is for visibility, not product complexity
- avoiding a separate frontend keeps the code inspectable

Key point:

> The role cares about production inference and Python/API debugging, not frontend scaffolding.

## If they ask: “How would you debug a customer issue?”

Open:

```text
docs/failure-tree.md
```

Explain the path:

1. Client/Python request shape
2. Auth/API response
3. OpenRouter routing constraints
4. Provider availability
5. Runtime timeout or stream interruption
6. Telemetry gaps
7. UI display bug

Key point:

> The failure tree keeps debugging practical instead of vague.

## If they ask: “What are the tests proving?”

Open:

```text
tests/test_response_handling.py
tests/test_routing_config.py
tests/test_eval_scoring.py
```

Explain:

- response/error handling is stable
- routing strategies are configured as expected
- deterministic eval scoring works

Key point:

> Tests cover the parts most likely to break during live debugging or route changes.

## Things not to over-explain

Avoid spending interview time on:

- NiceGUI internals
- FastAPI/Starlette implementation details under NiceGUI
- full SaaS architecture
- auth/multi-tenancy
- charting or UI polish
- elaborate eval methodology

## Final technical takeaway

> The implementation is intentionally small: UI calls scenarios, scenarios use routing and client logic, client streams from OpenRouter, telemetry records what happened, and evals close the loop on model selection.
