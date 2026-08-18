# UI/UX Plan - OpenRouter Production Inference Lab

## Design principle

The UI should not look like a generic chatbot. It should look like a compact inference operations console.

The user is the candidate/interviewer, not an end customer. The UI exists to make reasoning visible.

## Main screen structure

```text
+--------------------------------------------------------------+
| OpenRouter Production Inference Lab                          |
| Route, observe, recover, and evaluate model calls.            |
+--------------------------------------------------------------+

+------------------------------+-------------------------------+
| 1. Request                    | 2. Strategy                    |
| Prompt                       | Strategy selector              |
| [textarea]                   | Default / Cost / Latency       |
|                              | Failure demo toggle            |
| [Run Inference]              | Cache/repeat demo note         |
+------------------------------+-------------------------------+

+------------------------------+-------------------------------+
| 3. Streaming Response         | 4. Request Telemetry           |
| Live streamed output          | Model                          |
|                              | Provider                       |
|                              | Latency                        |
|                              | Tokens                         |
|                              | Cost                           |
|                              | Fallback                       |
|                              | Cache / repeat behavior        |
|                              | Langfuse trace                 |
+------------------------------+-------------------------------+

+--------------------------------------------------------------+
| 5. Run History / Comparison                                   |
| Previous runs with model, strategy, latency, cost, result     |
+--------------------------------------------------------------+

+--------------------------------------------------------------+
| 6. Eval Summary                                               |
| Run evals / View latest result                                |
+--------------------------------------------------------------+
```

## UI sections

### Header

Recommended copy:

```text
OpenRouter Production Inference Lab
A small Python demo for routing, fallback, cost, latency, traces, and evals.
```

Optional subtitle:

```text
A model call is easy. Operating inference is the real problem.
```

### Prompt panel

Fields:

- Prompt textarea
- Optional sample prompt dropdown
- Run button

Sample prompts:

1. “Explain eventual consistency to a backend engineer.”
2. “Summarize this incident report for a customer.”
3. “Classify this support ticket by severity.”
4. “Extract action items from this meeting note.”

Design intent:

- Prompts should imply real FDE/customer workflows.
- Avoid toy examples that weaken the production story.

### Strategy panel

Controls:

- `Default`
- `Cost optimized`
- `Latency optimized`
- `Custom / explicit route`
- `Simulate failure`
- `Repeat previous prompt`

Each strategy should have a short explanation.

Example:

```text
Default
Balanced route for general quality and availability.

Cost optimized
Prefer lower-cost model/provider choices. Validate quality before adopting.

Latency optimized
Prefer faster routes. Useful for interactive UX.

Custom
Use explicit model/provider preferences for debugging or customer-specific constraints.
```

Design intent:

- Make routing decisions inspectable.
- Avoid magical “best model” language.

### Streaming response panel

States:

1. Empty
2. Streaming
3. Complete
4. Failed then fallback
5. Failed unrecovered

During streaming:

```text
Streaming response...
```

After completion:

```text
Completed in 842 ms
```

If fallback occurred:

```text
Completed via fallback route after primary route failed.
```

Design intent:

- Streaming should visibly prove API integration.
- The response panel should remain secondary to operational metadata.

### Telemetry panel

| Field | Purpose |
|---|---|
| Strategy | Shows selected routing policy |
| Model | Shows actual model used |
| Provider | Shows provider when available |
| Latency | Makes performance visible |
| Tokens | Shows usage behavior |
| Cost | Supports price/performance reasoning |
| Fallback | Shows whether recovery happened |
| Cache / repeat | Reports observed behavior honestly |
| Trace | Links to Langfuse when enabled |
| Status | Success, failure, fallback success, tracing disabled |

Important UX rule:

> If metadata is unavailable, say “Unavailable from selected route/provider,” not “N/A” without explanation.

Example:

```text
Cost: unavailable from selected provider metadata
Cache: no cache metadata returned; showing observed repeat latency only
Trace: disabled — Langfuse credentials not configured
```

### Run history / comparison

Columns:

| Run | Strategy | Model | Latency | Tokens | Cost | Fallback | Trace |
|---|---|---|---|---|---|---|---|

Purpose:

- Makes routing/cost comparison visible.
- Lets the candidate compare cost/latency live.
- Gives the interviewer concrete data to ask about.

Example insight row:

```text
Cost strategy reduced estimated cost but increased latency by 310 ms.
```

Keep this simple. Do not add charts until the core demo works.

### Eval summary panel

Controls:

- `Run eval set`
- `View latest result`

Display:

| Case | Strategy | Pass | Score | Latency | Cost | Trace |
|---|---|---|---|---|---|---|

Summary example:

```text
Default strategy: 4/5 passed, $0.0021 total, 1.4s avg latency
Cost strategy: 4/5 passed, $0.0008 total, 1.9s avg latency
```

Design intent:

- Evals prove decision discipline.
- Avoid overbuilding an eval dashboard.

## Required UI states

### Empty state

```text
Run an inference request to see streaming output, route metadata, and telemetry.
```

### Loading / streaming state

```text
Streaming from OpenRouter...
```

Show partial response progressively.

### Success state

```text
Request completed successfully.
```

### Fallback success state

```text
Primary route failed. Fallback route completed successfully.
```

Display both attempts.

### Failure state

```text
Request failed before fallback could complete.
```

Include:

- short error type
- likely source
- next debugging step

Example:

```text
Authentication failed.
Check OPENROUTER_API_KEY in your environment.
```

### Tracing disabled state

```text
Langfuse tracing disabled.
Set LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and LANGFUSE_HOST to enable traces.
```

### Metadata unavailable state

```text
Cost metadata was not returned for this route/provider.
```

## UI/UX acceptance criteria

- [ ] The first screen explains the demo’s purpose in one sentence.
- [ ] The UI is organized around inference operation: request, strategy, response, telemetry, comparison, evals.
- [ ] The primary action is clearly labeled `Run Inference`.
- [ ] Strategy options include short explanations of their tradeoffs.
- [ ] The response panel shows streaming progress clearly.
- [ ] The telemetry panel updates after each run.
- [ ] The run history allows side-by-side comparison of recent runs.
- [ ] Fallback state uses explicit language: primary failed, fallback succeeded.
- [ ] Simulated failure is labeled as simulated.
- [ ] Error messages include a likely cause or next debugging step.
- [ ] Empty states explain what to do next.
- [ ] Disabled tracing, missing metadata, and unavailable cache information are explained plainly.
- [ ] The UI avoids chatbot framing as the main product metaphor.
- [ ] The app can support the five-minute walkthrough without navigating away from the main screen.

## UX risks to avoid

### Risk 1: It becomes “just a chatbot”

Avoid centering the design around the generated answer. The generated answer is evidence that streaming works, but the demo’s real value is the operational metadata.

Fix: make telemetry visually equal to or more important than the response.

### Risk 2: It overclaims caching

Cache behavior may vary by provider/path.

Fix: use careful language:

```text
Cache metadata returned: hit
```

or:

```text
No cache metadata returned. Showing observed repeat behavior only.
```

### Risk 3: Fallback looks fake or hidden

If fallback is simulated, hiding that would damage trust.

Fix: label it clearly:

```text
Simulated primary failure for demo reproducibility.
Fallback route completed successfully.
```

### Risk 4: UI polish distracts from code

The interview value is the operating model and Python implementation.

Fix: keep the UI clean, small, and inspectable. No separate frontend. No charting library unless absolutely necessary.
