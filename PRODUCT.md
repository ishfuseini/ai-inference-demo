# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Python 3.12+, NiceGUI, httpx, Langfuse Python SDK, uv, Ruff, pytest. The stack is established by the existing codebase and project documentation.

## Users

**Primary:** The candidate (Forward Deployed Engineer applicant) drives the demo — runs live OpenRouter calls, switches routing strategies, triggers fallback, inspects telemetry, and presents eval results during the interview.

**Secondary:** The interviewer (FDE / hiring manager) reads the repo, watches the five-minute walkthrough, asks probing questions, and may pair-debug the Python implementation.

## Product Purpose

A self-contained Python demo that makes production inference behavior visible and defensible in a five-minute interview demo. It is not a chatbot or SaaS app — it is an inspectable local lab showing how model calls behave when they must be operated, debugged, compared, and explained.

The demo proves the four production inference verbs: **routing, fallback, caching, cost optimization** — plus **evals** and **observability** through Langfuse traces.

Success means: an interviewer can understand what the project demonstrates in 30 seconds, see routing/streaming/fallback/cost/cache/traces working in 5 minutes, and open the Python implementation for a 15+ minute technical walkthrough.

Beyond the interview, the repo also serves as a public portfolio piece demonstrating production inference fluency.

## Positioning

The demo uses OpenRouter directly via HTTPS Chat Completions requests — it does not hide OpenRouter-specific routing or metadata behind another inference router. This direct integration is the core differentiator: it proves the candidate can operate the exact layer OpenRouter sells.

The product is an operating surface for inference, not a chatbot. The main product of the screen is operational visibility: route, latency, cost, fallback, cache/repeat behavior, trace, and eval comparison — not just the generated text.

## Operating Context

- **Environment:** Local Python app launched via `uv run python app.py`, rendering a NiceGUI browser UI.
- **Credentials:** `OPENROUTER_API_KEY` required; three Langfuse variables optional. The app reads exported environment variables only, never `.env` files.
- **Demo flow:** Four scenarios — Ship a Model Call → Make It Reliable → Make It Economical → Make Changes Safely.
- **Interview artifacts:** Live UI, streamed responses, telemetry panels, run history/comparison, eval output, Langfuse trace links, and a whiteboard failure tree (`docs/failure-tree.md`).
- **Supporting docs:** `docs/specs/quickstart.md` (eight validation steps), `docs/ux/demo-script.md` (30-second pitch + timed five-minute sequence).
- **Quality gates:** `uv run pytest`, `uv run ruff check .`.

## Capabilities and Constraints

### Capabilities

- Streaming OpenRouter Chat Completions requests with progressive token display
- Named routing strategies: default, cost-oriented, latency-oriented, custom
- Fallback behavior with both failed primary and successful fallback attempts preserved and visible
- Cost, latency, token usage, provider, and model metadata surfaced per run
- Cache/repeat behavior reported honestly from returned metadata
- Deterministic eval cases (3–5) with pass/fail scoring across at least two strategies or models
- Optional Langfuse tracing with visible disabled state when credentials are absent
- Run history for side-by-side comparison of recent runs
- Single-screen experience supporting the full five-minute walkthrough without navigation

### Constraints

- Not a production system: no auth, multi-tenancy, scale, or HA
- No database or background worker queue
- No separate JavaScript frontend or backend API service
- No Docker requirement for the core demo (Dockerfile and fly.toml exist for optional deployment)
- FastAPI is only a NiceGUI implementation detail, not a product layer
- Default prompts and eval cases must remain small and bounded
- Metadata honesty: token, cost, provider, router, and cache fields must distinguish unavailable values from zero values
- The app never claims a cache hit unless metadata or route behavior supports that claim
- Simulated failure must be labeled as simulated

## Brand Commitments

- **Name:** OpenRouter Production Inference Lab
- **Voice:** Technical, honest, operating-surface. Not marketing. Not chatbot.
- **Existing design system:** `docs/design/DESIGN.md` defines a shared visual language: clean, technical, approachable, lightweight. Primary color `#7B23D4` (purple), lavender background `#EEECFA`, surface `#F0EEF1`, dark text `#261F2E`.
- **Identity constraint:** The UI avoids chatbot framing as the main product metaphor.

## Evidence on Hand

- `evals/cases.json` — checked-in deterministic eval cases
- `data/api-complaint-eval.csv` — eval dataset for API complaint classification
- `data/api-complaint-rubric.md` — scoring rubric for the eval dataset
- `docs/failure-tree.md` — whiteboard failure tree for debugging a failed or degraded request
- `docs/ux/demo-script.md` — 30-second pitch and timed five-minute walkthrough script
- `docs/ux/demo-narrative.md` — story structure and interviewer takeaway
- `docs/ux/screen-spec.md` — single-screen layout and component specification
- `docs/specs/acceptance-criteria.md` — implementation-focused acceptance criteria across demo, eval, UI/UX, and repository categories
- `docs/architecture.md` — component boundaries and data flow
- Absences: No real customer testimonials, benchmarks, or press — future work must not fabricate these.

## Product Principles

1. **Make inference behavior visible.** The operational metadata around a response matters as much as the response itself.
2. **Be honest about missing data.** Unavailable metadata is explicitly distinguished from zero values; cache claims require evidence.
3. **Show the failure, don't hide it.** Fallback preserves the failed primary attempt; simulated failure is labeled as simulated.
4. **Use OpenRouter directly.** Never hide OpenRouter-specific routing, provider preferences, or metadata behind another abstraction.
5. **Stay inspectable.** The code must remain small enough for an interviewer to read top-to-bottom in five minutes.

## Accessibility & Inclusion

Follow standard web accessibility best practices for the NiceGUI browser UI. No specific conformance standard (e.g., WCAG 2.1 AA) is required, but the interface should remain operable and understandable for a reviewer using keyboard navigation or assistive technology during the interview.