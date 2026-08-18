# Screen Spec - OpenRouter Production Inference Lab

## Purpose

This document specifies the single-screen demo experience. The screen should support the full five-minute walkthrough without requiring navigation.

## Screen principle

The screen is an inference operations console, not a chatbot.

The generated answer matters, but the main product of the screen is operational visibility: route, latency, cost, fallback, cache/repeat behavior, trace, and eval comparison.

## Page layout

```text
Header
Request + Strategy
Streaming Response + Telemetry
Run History / Comparison
Eval Summary
```

## Header

### Required content

Title:

```text
OpenRouter Production Inference Lab
```

Subtitle:

```text
Route, observe, recover, and evaluate model calls.
```

Optional supporting line:

```text
A model call is easy. Operating inference is the real problem.
```

### Intent

The header should explain the demo before the candidate says anything.

## Request panel

### Components

- Prompt label
- Prompt textarea
- Sample prompt selector
- Primary action button

### Labels

Prompt label:

```text
Prompt
```

Textarea placeholder:

```text
Ask a production-style question, classification task, or summarization task...
```

Sample prompt selector label:

```text
Sample prompt
```

Primary button:

```text
Run Inference
```

### Sample prompts

- Explain eventual consistency to a backend engineer.
- Summarize this incident report for a customer.
- Classify this support ticket by severity.
- Extract action items from this meeting note.

### Behavior

- The button is enabled when the prompt has non-whitespace text.
- Clicking `Run Inference` starts a streaming request.
- During streaming, the button should show an in-progress state or be disabled to prevent accidental duplicate runs.

## Strategy panel

### Components

- Strategy selector
- Strategy explanation
- Failure simulation toggle
- Repeat previous prompt action or note

### Strategy options

#### Default

Label:

```text
Default
```

Description:

```text
Balanced route for general quality and availability.
```

#### Cost optimized

Label:

```text
Cost optimized
```

Description:

```text
Prefer lower-cost model/provider choices. Validate quality before adopting.
```

#### Latency optimized

Label:

```text
Latency optimized
```

Description:

```text
Prefer faster routes for interactive use cases.
```

#### Custom / explicit route

Label:

```text
Custom
```

Description:

```text
Use explicit model/provider preferences for debugging or customer-specific constraints.
```

### Failure simulation

Label:

```text
Simulate primary route failure
```

Helper text:

```text
For a reproducible demo. The UI will label this as simulated.
```

### Intent

The user should understand what tradeoff they are selecting before the run starts.

## Streaming response panel

### Empty state

```text
Run an inference request to see streaming output.
```

### Streaming state

```text
Streaming from OpenRouter...
```

Behavior:

- Append streamed tokens progressively.
- Preserve partial output if the stream fails.
- Do not replace a partial failure with a generic error unless the partial output is also shown or intentionally cleared with explanation.

### Success state

```text
Request completed successfully.
```

### Fallback success state

```text
Completed via fallback route after primary route failed.
```

### Failure state

```text
Request failed before fallback could complete.
```

The panel should include enough information to support debugging, not just user reassurance.

## Telemetry panel

### Fields

| Field | Required behavior |
|---|---|
| Status | Shows idle, streaming, success, fallback success, or failed |
| Strategy | Shows selected strategy |
| Model | Shows actual model used when available |
| Provider | Shows actual provider when available |
| Latency | Shows observed request duration |
| Tokens | Shows token usage when available |
| Cost | Shows cost when available |
| Fallback | Shows yes/no and route details when relevant |
| Cache / repeat | Shows returned cache metadata or observed repeat behavior |
| Trace | Shows Langfuse trace link or disabled state |

### Metadata unavailable copy

```text
Unavailable from selected route/provider.
```

### Cost unavailable copy

```text
Cost metadata was not returned for this route/provider.
```

### Cache unavailable copy

```text
No cache metadata returned. Showing observed repeat behavior only.
```

### Tracing disabled copy

```text
Langfuse tracing disabled. Configure Langfuse credentials to enable trace links.
```

### Intent

Telemetry should be visually prominent enough that the interviewer sees production inference behavior, not just generated text.

## Run history / comparison panel

### Purpose

Support the routing and cost/latency comparison portion of the demo.

### Columns

| Column | Notes |
|---|---|
| Run | Human-readable sequence number |
| Strategy | Requested strategy |
| Model | Actual model used |
| Provider | Actual provider if available |
| Latency | Observed latency |
| Tokens | Token usage if available |
| Cost | Cost if available |
| Fallback | Yes/no |
| Trace | Link or disabled marker |

### Empty state

```text
Previous runs will appear here for cost, latency, and route comparison.
```

### Insight copy examples

```text
Cost strategy reduced estimated cost but increased latency.
```

```text
Latency strategy responded faster but should still be checked against eval quality.
```

```text
Fallback route completed successfully after primary failure.
```

## Eval summary panel

### Purpose

Show that model or routing changes are evaluated before being treated as safe.

### Components

- `Run eval set` button
- Latest result summary
- Per-case result table

### Columns

| Column | Notes |
|---|---|
| Case | Eval case name |
| Strategy | Strategy/model tested |
| Result | Pass/fail |
| Score | Deterministic score or optional judge score |
| Latency | Observed latency |
| Cost | Cost if available |
| Trace | Trace link if enabled |

### Empty state

```text
Run the eval set to compare quality, latency, and cost across model choices.
```

### Summary example

```text
Default strategy: 4/5 passed, $0.0021 total, 1.4s average latency.
Cost strategy: 4/5 passed, $0.0008 total, 1.9s average latency.
```

## Error message patterns

### Authentication error

```text
Authentication failed. Check OPENROUTER_API_KEY in your environment.
```

### Rate limit

```text
OpenRouter returned a rate limit response. Wait briefly, lower request volume, or switch route if appropriate.
```

### Timeout

```text
Primary route timed out. Fallback route will be attempted if configured.
```

### Provider/model unavailable

```text
Selected model or provider was unavailable. Check routing constraints or use fallback.
```

### Unknown error

```text
Request failed unexpectedly. Inspect the trace, client logs, and failure tree.
```

## Acceptance checks

- [ ] The screen supports the full demo without navigation.
- [ ] The generated answer is not the only visible success signal.
- [ ] Strategy choice is visible before and after the run.
- [ ] Actual model/provider used is visible when available.
- [ ] Failure and fallback are distinguishable states.
- [ ] Simulated failure is labeled as simulated.
- [ ] Missing metadata is explained plainly.
- [ ] Tracing disabled state is clear and non-blocking.
- [ ] Run history supports at least basic cost/latency comparison.
- [ ] Eval summary supports evidence-based model selection discussion.
