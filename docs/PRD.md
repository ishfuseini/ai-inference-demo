# PRD - OpenRouter FDE Interview Demo ("Inference in Production")

## 1. Summary

A self-contained demo repo that proves the candidate can operate the exact layer OpenRouter sells: unified inference with **routing, fallback, caching, and cost optimization** plus **evals and observability**. It is the show-don't-tell artifact for the Forward Deployed Engineer interview.

The demo is a Python-first interactive inference lab. A NiceGUI interface runs live OpenRouter calls, streams responses, exposes routing/fallback/cost/latency behavior, and links each run to Langfuse traces. The code remains small enough for an interviewer to inspect during a technical walkthrough.

**One-liner:** A streaming OpenRouter demo that routes across models/providers, falls back on failure or latency, shows repeat/cache behavior where available, traces every call in Langfuse, and scores outputs against a small eval set.

## 2. Why This Exists

- The role's interview filter is "can you debug production code daily and reason about routing/fallback/caching/cost."
- The candidate's titles are Solutions Architect, so the code bar must be proven in code, not asserted.
- The application already promised "a short streaming OpenRouter sample with routing, fallback and Langfuse-traced evals."
- The demo should prove direct OpenRouter fluency rather than hiding OpenRouter behind another inference router.
- The project should be honest: a cleaned-up, readable slice of real inference work, scoped tightly enough to run during an interview.

The intended interviewer experience:

- **30 seconds:** Understand what the project demonstrates.
- **5 minutes:** See routing, streaming, fallback, cost, cache/repeat behavior, and observability working.
- **15+ minutes:** Open the Python implementation and discuss API behavior, failure handling, model selection, tradeoffs, and debugging.

## 3. Core Story

The demo answers one question:

> What happens when a model call becomes something you actually have to operate?

The project progresses through four scenarios.

### Scenario 1 - Ship a Model Call

Send a real streaming inference request through OpenRouter.

Demonstrates:

- OpenRouter API integration
- OpenRouter's OpenAI-compatible request format
- Streaming responses
- Response parsing
- Usage metadata

### Scenario 2 - Make It Reliable

Introduce routing constraints or failure and demonstrate recovery.

Demonstrates:

- Model/provider preferences
- Fallback behavior
- Timeout/error handling
- Failure visibility
- Graceful degradation

### Scenario 3 - Make It Economical

Run equivalent workloads with different routing/model choices and expose the resulting tradeoffs.

Demonstrates:

- Cost
- Latency
- Token usage
- Model selection
- Cache behavior where applicable
- Price/performance reasoning

### Scenario 4 - Make Changes Safely

Run a small evaluation set across model choices and inspect the results.

Demonstrates:

- Evals
- Langfuse traces
- Quality comparison
- Latency/cost comparison
- Evidence-based model selection

The point is not that one model is "best." The point is that production inference involves choosing among quality, latency, reliability, and cost.

## 4. Goals / Non-Goals

### Goals

- Prove the four JD verbs: routing, fallback, caching, cost optimization.
- Prove evals through quality scoring and observability through Langfuse traces.
- Use OpenRouter directly from Python.
- Use NiceGUI as the lightweight browser UI.
- Use TailwindCSS utility classes through NiceGUI for simple styling.
- Use `uv` for dependency management and command execution.
- Use Ruff for linting and formatting.
- Use pytest for focused tests.
- Readable top-to-bottom in five minutes by a hiring manager.
- Support a five-minute walkthrough plus a whiteboard failure tree.
- Keep the repo honest, inspectable, and portable.

### Non-Goals

- Not a production system.
- No authentication, multi-tenancy, scale, or HA.
- Not a full eval harness.
- No golden-set pipeline or full regression suite.
- Not a SaaS product.
- No separate JavaScript frontend.
- No separate backend API service.
- No database or background worker queue.
- No Docker requirement for the core demo.
- Not a tutorial on basic OpenRouter API usage.

## 5. Personas

- **Interviewer (FDE / hiring manager):** reads the repo, asks "walk me through routing/fallback/caching/cost," may pair-debug.
- **Candidate:** drives the technical interview with the repo, live UI, traces, eval output, and failure tree.

## 6. Demo Experience

The primary interface is a lightweight NiceGUI app.

NiceGUI keeps the project Python-first while making runtime behavior visible in a browser: prompt input, scenario controls, streamed output, telemetry, trace links, and eval results. NiceGUI runs on top of FastAPI/Starlette internally, but that is only a framework implementation detail. The demo should not introduce a separate FastAPI service or present FastAPI as a distinct architecture layer.

### Main View

```text
+------------------------------------------------------+
| OpenRouter Production Inference Lab                  |
+------------------------------------------------------+
| Prompt                                               |
| +--------------------------------------------------+ |
| | Explain eventual consistency...                  | |
| +--------------------------------------------------+ |
|                                                      |
| Strategy                                             |
| ( ) Default    ( ) Cost    ( ) Latency    ( ) Custom |
|                                                      |
| [ Run Inference ]                                    |
+---------------------------+--------------------------+
| Streaming Response        | Request Telemetry        |
|                           |                          |
| Eventual consistency...   | Model: ...               |
|                           | Provider: ...            |
|                           | Latency: 842 ms          |
|                           | Tokens: 428              |
|                           | Cost: $0.00xx            |
|                           | Fallback: No             |
|                           | Cache: Miss              |
|                           | Trace: ...               |
+---------------------------+--------------------------+
```

The UI exists to expose the inference behavior, not abstract it away.

## 7. Scope

### Phase 0 - Minimal

| # | Capability | Detail |
|---|---|---|
| 1 | Streaming call | Streaming chat completion through OpenRouter |
| 2 | Routing | Multiple OpenRouter model/provider strategies |
| 3 | Fallback | Primary OpenRouter model/provider route to fallback route on failure or latency timeout |
| 4 | Observability | Langfuse trace with latency, cost, tokens, scenario, success/failure |
| 5 | Minimal eval | 3-5 cases with deterministic pass/fail scoring |
| 6 | NiceGUI UI | Prompt, scenario selector, streamed response, telemetry panel |

### Phase 1 - Polished

| # | Capability | Detail |
|---|---|---|
| 7 | Cache/repeat demo | Show repeat prompt behavior where OpenRouter/provider caching metadata is available; otherwise show observed repeat latency/cost without inventing cache claims |
| 8 | Richer evals | Optional LLM-as-judge scoring plus a few quality cases |
| 9 | README | The story: what it does, why, how to run, what it proves |
| 10 | Architecture diagram | OpenRouter routing/fallback/latency/cost matrix |
| 11 | Failure tree | Client to OpenRouter to provider to telemetry diagnosis path |
| 12 | Repo hygiene | Clean structure, typed, env-var secrets, one-command run, Ruff, pytest |

## 8. Architecture

```text
                    +-----------------------------+
                    |        NiceGUI app          |
                    | prompt + scenarios + UI     |
                    +--------------+--------------+
                                   |
                                   v
                    +-----------------------------+
                    |    Python service layer     |
                    | streaming orchestration     |
                    | routing config              |
                    | fallback handling           |
                    | telemetry normalization     |
                    +--------------+--------------+
                                   |
                                   | OpenRouter API
                                   v
                    +-----------------------------+
                    |         OpenRouter          |
                    | routing + providers         |
                    | fallback + usage/cost       |
                    +-----+-----------+-----------+
                          |           |
                          v           v
                    Model/provider  Model/provider
                    primary         fallback

                    +-----------------------------+
                    |          Langfuse           |
                    | traces + latency + cost     |
                    | tokens + eval scores        |
                    +-----------------------------+
```

OpenRouter owns the inference routing story in this demo. The Python service layer only prepares requests, handles streams/errors, normalizes metadata, records traces, and exposes results to the UI.

## 9. Components / Repo Layout

```text
openrouter-fde-demo/
|-- README.md              # the 5-minute story
|-- Makefile               # make demo / make eval / make check
|-- pyproject.toml         # uv project config
|-- uv.lock                # locked dependencies
|-- .env.example           # OPENROUTER_API_KEY, LANGFUSE_*
|-- app.py                 # starts the NiceGUI app
|
|-- src/
|   |-- openrouter_demo/
|       |-- __init__.py
|       |-- client.py      # OpenRouter streaming + errors + metadata
|       |-- config.py      # env vars and defaults
|       |-- evals.py       # eval cases + scoring
|       |-- models.py      # typed result/telemetry structures
|       |-- routing.py     # model/provider strategies + fallbacks
|       |-- scenarios.py   # deterministic demo scenarios
|       |-- telemetry.py   # Langfuse + normalized runtime metrics
|       |-- ui.py          # NiceGUI views/components
|
|-- evals/
|   |-- cases.json         # the eval set
|
|-- docs/
|   |-- architecture.md    # routing/latency/cost matrix
|   |-- failure-tree.md    # client -> OpenRouter -> provider diagnosis
|
|-- tests/
    |-- test_response_handling.py
    |-- test_routing_config.py
    |-- test_eval_scoring.py
```

### `app.py`

Thin entry point that loads configuration, registers the NiceGUI UI, and starts the local demo server.

### `ui.py`

NiceGUI screen composition for prompt input, scenario selection, streaming display, telemetry display, trace links, and TailwindCSS styling classes.

Business/inference logic should remain outside the UI.

### `client.py`

OpenRouter integration for request construction, streaming, timeout handling, API exceptions, response normalization, and available usage metadata.

### `routing.py`

Reusable inference strategies:

- default,
- cost-oriented,
- latency-oriented,
- explicit model/provider preferences,
- fallback configuration.

### `telemetry.py`

Normalizes runtime information:

- latency,
- tokens,
- cost,
- provider/model,
- cache status where available,
- fallback status,
- trace identifiers.

### `scenarios.py`

Deterministic demo scenarios. The UI should call scenarios rather than embedding demo behavior directly.

### `evals.py`

Runs the small evaluation suite and records result, quality score, latency, cost, model/provider, and Langfuse trace.

## 10. Stack

The stack is intentionally narrow:

| Layer | Choice | Purpose |
|---|---|---|
| Inference | OpenRouter | Direct model/provider routing, fallback, streaming, usage, and cost behavior |
| Language | Python | Clear implementation surface for API handling, scenarios, telemetry, and evals |
| UI | NiceGUI | Python-first interactive browser UI |
| Styling | TailwindCSS | Lightweight utility styling through NiceGUI |
| Observability | Langfuse | Traces, latency, usage, cost, and eval inspection |
| Package/runtime | uv | Dependency management and command execution |
| Lint/format | Ruff | One tool for linting and formatting |
| Tests | pytest | Focused tests around response handling, routing config, and eval scoring |

The dependency list should stay boring:

```toml
[project]
dependencies = [
    "nicegui",
    "langfuse",
]

[dependency-groups]
dev = [
    "pytest",
    "ruff",
]
```

If implementation uses an OpenAI-compatible Python client package or a small HTTP helper for OpenRouter calls, document it as an implementation dependency, not an architectural layer.

## 11. Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Language | Python | Demonstrates hands-on Python while fitting naturally with inference/eval tooling |
| Inference layer | OpenRouter directly | The project exists specifically to demonstrate OpenRouter's production inference value |
| UI | NiceGUI | Makes runtime behavior visible without creating a separate frontend project |
| Styling | TailwindCSS via NiceGUI | Gives enough UI polish without adding a frontend build system |
| API surface | No separate service in v1 | Keeps the architecture focused on inference behavior, not backend scaffolding |
| Observability | Langfuse | Makes traces, latency, usage, cost, and eval behavior inspectable |
| Eval depth | Minimal deterministic evals first | Proves the concept without building a full harness |
| LLM-as-judge | Optional polish | Useful later, unnecessary for the core proof |
| Secrets | env vars, `.env.example` only | Never commit keys |
| Cost | Small models + explicit run discipline | Keep demo runs cheap and predictable |

## 12. Acceptance Criteria

- [ ] `uv sync` installs the project.
- [ ] `uv run python app.py` launches the NiceGUI UI.
- [ ] A user can execute a real streaming OpenRouter request.
- [ ] Streaming tokens appear progressively in the UI.
- [ ] The completed request displays available model/provider metadata.
- [ ] The request displays observed latency.
- [ ] The request displays token usage.
- [ ] The request displays available cost information.
- [ ] At least one routing/model-selection strategy can be demonstrated.
- [ ] At least one reproducible fallback/failure scenario can be demonstrated.
- [ ] Failure and recovery are visible rather than silently hidden.
- [ ] Repeat/cache behavior can be demonstrated where supported by the selected OpenRouter path.
- [ ] Langfuse receives traces for demo calls when Langfuse credentials are configured.
- [ ] The app still runs when Langfuse credentials are absent, with tracing clearly marked disabled.
- [ ] `make eval` or an equivalent `uv` command runs the small evaluation set.
- [ ] Eval output compares quality, latency, and cost.
- [ ] README explains routing/fallback/caching/cost in five minutes or less.
- [ ] `docs/failure-tree.md` covers client to OpenRouter to provider diagnosis with a practical path.
- [ ] No secrets are committed.
- [ ] `.env.example` documents all required variables.
- [ ] Core response/error handling has focused tests.
- [ ] Routing config has focused tests.
- [ ] Eval scoring has focused tests.
- [ ] `uv run pytest` passes.
- [ ] `uv run ruff check .` passes.
- [ ] A reviewer can run it end-to-end with only `OPENROUTER_API_KEY` required and Langfuse credentials optional.
- [ ] The repository does not present FastAPI as a separate service.

## 13. Timeline

| Phase | Trigger | Effort |
|---|---|---|
| Phase 0 - Minimal | Apply now | ~2-4 hours |
| Phase 1 - Polished | Interview selected | 1-2 evenings |

## 14. Risks / Open Questions

- **Cost:** OpenRouter calls cost money. Mitigate with small models, explicit model defaults, and documented run discipline.
- **Fallback realism:** A real upstream/provider failure may not be reproducible on demand. Keep one real OpenRouter fallback path and allow a clearly labeled simulated failure trigger for demos.
- **Cache visibility:** Cache metadata and behavior may vary by selected OpenRouter route/provider. Report observed values rather than hard-code hit/miss claims.
- **Eval hardness:** LLM-as-judge adds a judge-model dependency. Keep it optional. Deterministic pass/fail scoring is the floor; judge scoring is polish.
- **UI scope:** NiceGUI should make the behavior visible, not become the project. Defer UI polish until the inference scenarios work.

## 15. Failure Tree

`docs/failure-tree.md` should describe a practical diagnosis path.

```text
Request failed
|
+-- Client / Python
|   +-- malformed request
|   +-- serialization
|   +-- streaming handling
|
+-- Authentication / API
|   +-- credentials
|   +-- rate limit
|   +-- request validation
|
+-- OpenRouter routing
|   +-- model unavailable
|   +-- provider unavailable
|   +-- routing constraint
|   +-- fallback behavior
|
+-- Runtime
|   +-- timeout
|   +-- latency spike
|   +-- interrupted stream
|
+-- Observability
|   +-- trace missing
|   +-- token/cost metadata missing
|   +-- eval result not recorded
|
+-- Application
    +-- response parsing
    +-- telemetry display
    +-- UI rendering
```

The candidate should be able to use this to explain how they would debug a customer's inference request from application to OpenRouter to provider and back through telemetry.

## 16. Demo Walkthrough

Target runtime: five minutes.

### 0:00-0:30 - Context

> A basic model call is easy. This demo shows what changes when inference becomes something you need to operate: routing, fallback, cost, latency, traces, and evals.

### 0:30-1:30 - Normal Streaming Request

Show prompt entry, streamed response, selected model/provider, latency, tokens, and cost.

### 1:30-2:30 - Routing / Optimization

Run the same prompt with a different strategy. Explain why model/provider choice changes, what tradeoff was made, and what telemetry changed.

### 2:30-3:30 - Failure / Fallback

Trigger the failure scenario. Show failed preferred route, fallback route, final successful response, and trace/error visibility.

### 3:30-4:30 - Eval / Comparison

Run the small eval set or show a saved recent result. Discuss pass/fail result, latency, cost, and model-selection decision.

### 4:30-5:00 - Code Inspection

Open:

- `client.py` for OpenRouter integration,
- `routing.py` for model/provider strategy,
- `telemetry.py` for normalized metadata,
- `evals.py` for decision-loop logic.

The desired final impression:

> This candidate understands OpenRouter's value proposition and can write/debug the Python code around it.

## 17. Scope Guardrails

The project should stay small enough to understand quickly.

When considering a new dependency, feature, or module, ask:

1. Does this demonstrate OpenRouter more clearly?
2. Does this demonstrate Python/API debugging more clearly?
3. Does this make the interview walkthrough stronger?
4. Can this be explained in less than one minute?

If the answer is no, defer it.

The repository should feel intentional, not scaffold-heavy. The strongest version of this project is a compact working demo with excellent observability and a clear failure story.
