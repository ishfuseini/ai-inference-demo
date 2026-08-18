# Demo Script - OpenRouter Production Inference Lab

## Purpose

This is the spoken walkthrough for the interview. The goal is to make the production inference story clear in 5 minutes, with shorter versions available if time is tight.

## 30-second elevator pitch

> A basic model call is easy. This demo shows what changes when inference becomes something you have to operate in production: routing, fallback, latency, cost, traces, and evals. It is a small Python-first OpenRouter lab that makes every model call inspectable instead of treating the generated response as the whole story.

## 2-minute compressed walkthrough

> This app sends a streaming request through OpenRouter and shows the operational metadata next to the response: actual model, provider when available, latency, tokens, cost, fallback status, and Langfuse trace.
>
> First I run a normal streaming request to prove the integration path. Then I run the same prompt with a different routing strategy to show how model/provider choice changes cost and latency. After that, I trigger a reproducible failure path so the primary route fails visibly and the fallback route completes. Finally, I run a tiny eval set to compare quality, latency, and cost before changing model defaults.
>
> The point is not that one model is always best. The point is that production inference requires a loop: route intentionally, observe what happened, recover from failure, measure quality, and make changes with evidence.

## 5-minute walkthrough

### 0:00-0:30 — Context

Say:

> Most LLM demos stop at “I got text back.” But in production, that is not enough. You need to know which model answered, what it cost, how long it took, whether fallback happened, and whether the output is good enough to ship.
>
> This is a small Python-first demo around OpenRouter. It is intentionally not a SaaS app. It is an inference operations lab.

Show:

- App title
- Prompt input
- Strategy controls
- Empty response and telemetry panels

Emphasize:

> The UI exists to expose inference behavior, not hide it behind a chatbot.

### 0:30-1:30 — Normal streaming request

Say:

> I’ll start with the simplest path: a real streaming OpenRouter request.

Action:

1. Choose or enter a practical prompt.
2. Select `Default` strategy.
3. Click `Run Inference`.
4. Let the response stream.

Say while streaming:

> The streaming output proves the API path is live, but the more important part is the telemetry being collected around the call.

Point to:

- model
- provider, if available
- latency
- tokens
- cost, if available
- trace link, if Langfuse is configured

Transition:

> Now that the baseline works, the production question becomes: should this be the route we use every time?

### 1:30-2:30 — Routing and optimization

Say:

> Now I’ll run the same prompt with a different routing strategy. This is where OpenRouter becomes useful operationally: I can reason about routing instead of hardcoding a single model forever.

Action:

1. Keep the same prompt.
2. Switch to `Cost optimized` or `Latency optimized`.
3. Run again.
4. Compare against the previous run.

Say:

> The tradeoff is visible here. A cheaper route may be slower or lower quality. A faster route may cost more. The right answer depends on the product constraint.

Point to:

- strategy label
- actual model used
- latency delta
- cost delta
- run history row

Key line:

> I am not claiming this strategy is universally better. I am showing how I would make the tradeoff inspectable.

### 2:30-3:30 — Failure and fallback

Say:

> Production inference fails in boring ways: bad request shape, auth problems, provider unavailability, model errors, rate limits, latency spikes, and interrupted streams. The important thing is to make failure visible and recovery deliberate.

Action:

1. Enable `Simulate failure` or select the failure scenario.
2. Run the prompt.
3. Show primary failure.
4. Show fallback success.

Say:

> This path is labeled as simulated so the demo is reproducible. I do not want fake reliability theater. I want to show the control flow: primary route failed, fallback route completed, and both attempts are visible.

Point to:

- failed primary route
- failure reason
- fallback model/route
- final status
- trace/error visibility

Key line:

> Fallback is not magic. If it happened, an operator should be able to see why.

### 3:30-4:30 — Evals and safe model changes

Say:

> Cost and latency optimization are only safe if quality remains acceptable. So the repo includes a tiny deterministic eval set. It is not a full benchmark harness; it is the smallest version of the decision loop.

Action:

1. Run evals or show latest eval results.
2. Compare model/strategy output.
3. Point to pass/fail, latency, cost, and traces.

Say:

> This is how I would avoid changing model defaults based only on vibes. If cost strategy is cheaper but fails a key case, that matters. If it passes the same cases at lower cost, that is evidence for switching.

Key line:

> The model decision should be evidence-based, not brand-based.

### 4:30-5:00 — Code inspection

Say:

> The repo is intentionally small so we can inspect the production inference layer directly.

Open:

- `client.py` for OpenRouter streaming, request construction, errors, and metadata
- `routing.py` for route/model/provider strategy definitions
- `telemetry.py` for normalized runtime metrics and Langfuse traces
- `scenarios.py` for deterministic demo paths
- `evals.py` for scoring and comparison logic

Final line:

> That is the shape of production inference: request, route, observe, recover, measure, and change safely.

## Likely interviewer questions

### Why NiceGUI?

> It keeps the demo Python-first while still giving a browser UI for streaming, telemetry, and eval results. A separate frontend would distract from the OpenRouter/Python debugging layer this interview cares about.

### Why not build a full eval harness?

> Because the demo needs to be inspectable. The goal is to prove the decision loop with 3-5 deterministic cases, not to create a benchmark product.

### What if provider cache metadata is unavailable?

> Then the UI should say that plainly. We can show observed repeat latency/cost behavior, but should not claim a cache hit unless the route/provider exposes evidence for it.

### What if Langfuse credentials are missing?

> The app should still run. Tracing is optional, and the UI should clearly mark tracing as disabled.

### What makes this OpenRouter-specific?

> The demo keeps OpenRouter as the direct inference layer. Routing, fallback, model/provider strategy, usage metadata, and cost/latency tradeoffs are the center of the experience.

### What would you debug first if a request failed?

> I would check the failure tree: client request construction, credentials/API response, OpenRouter routing constraints, provider availability, runtime timeout/stream interruption, telemetry recording, then UI rendering.
