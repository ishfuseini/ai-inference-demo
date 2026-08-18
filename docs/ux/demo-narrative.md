# Demo Narrative - OpenRouter Production Inference Lab

## Core narrative

> A model call is easy. Production inference is the hard part.

This demo progresses from “I can call an LLM” to “I can operate inference under real constraints.”

The desired interviewer takeaway:

> This candidate understands OpenRouter’s production value: routing, fallback, cost control, observability, and eval-driven model selection — and can implement/debug the Python layer around it.

## Story structure

### Situation

Most demos stop at a successful model response. In production, success means more than getting text back. You need to know which model answered, what it cost, how long it took, whether it fell back, and whether the output is good enough.

### Complication

Once real users depend on inference, every request becomes an operational question: what if the preferred provider is slow, unavailable, expensive, or lower quality than expected?

### Resolution

This demo turns a single model call into an inspectable production inference loop: route intentionally, stream visibly, fail over clearly, trace every run, compare cost/latency/quality, and make model changes with evidence.

## Five-minute walkthrough

### 0:00–0:30 — Frame the problem

Say:

> This is a small Python-first inference lab built around OpenRouter. The point is not to build a SaaS app. The point is to make production inference behavior visible: routing, fallback, cost, latency, traces, and evals.

Show:

- App title
- Prompt area
- Scenario/strategy controls
- Empty telemetry panel

Intent: establish that the UI is an operating surface, not a chatbot.

### 0:30–1:30 — Ship a model call

Say:

> First, here’s the baseline: a streaming OpenRouter request. I’m showing the streamed output and the operational metadata next to it.

Show:

- Enter or use a sample prompt
- Click **Run Inference**
- Tokens stream progressively
- Telemetry fills in: model, provider if available, latency, tokens, cost, trace link

Point to make:

> Even at this stage, I’m not treating the response as enough. The important part is the metadata around the response.

### 1:30–2:30 — Route intentionally

Say:

> Now I’ll run the same workload with a different strategy. The goal is to make the tradeoff explicit: lower cost, lower latency, or default quality.

Show:

- Same prompt
- Switch strategy from `Default` to `Cost` or `Latency`
- Run again
- Compare previous and current metrics

Point to make:

> OpenRouter lets me reason at the routing/model/provider layer instead of hardcoding one model forever.

Example comparison copy:

```text
Cost strategy selected a cheaper route.
Latency improved by 280 ms.
Estimated cost decreased by 42%.
Output quality should be validated before adopting this as default.
```

### 2:30–3:30 — Make failure visible

Say:

> Production inference fails in boring ways: unavailable model, timeout, bad route, interrupted stream. The important part is not hiding the failure — it’s surfacing what happened and recovering deliberately.

Show:

- Trigger clearly labeled failure scenario
- Preferred route fails
- Fallback route succeeds
- UI displays both failed primary attempt and successful fallback attempt

Point to make:

> Fallback is not magic. I want the operator to see that fallback happened, why it happened, and what route recovered.

Recommended UI copy:

```text
Simulated failure triggered for demo.
Primary route failed before completion.
Fallback route completed successfully.
```

### 3:30–4:30 — Make changes safely with evals

Say:

> Routing and cost optimization are only safe if quality stays acceptable. So this repo includes a tiny eval loop: not a full benchmark harness, but enough to show how I’d compare model choices before changing defaults.

Show:

- Run eval set or display a saved recent eval result
- Compare pass/fail, latency, cost, selected model/provider, and trace link

Point to make:

> The model decision is evidence-based. I’m not saying one model is best — I’m showing how I would decide under constraints.

### 4:30–5:00 — Open the code

Say:

> The repo is intentionally small. The interesting parts are separated: OpenRouter streaming in `client.py`, routing policy in `routing.py`, telemetry normalization in `telemetry.py`, and eval logic in `evals.py`.

Show:

- `client.py`
- `routing.py`
- `telemetry.py`
- `evals.py`

Final line:

> That’s the shape of production inference: request, route, observe, recover, measure, and change safely.
