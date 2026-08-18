# Data Model: OpenRouter Inference Lab

## Entity: InferenceRun

Represents one prompt execution from request start through stream completion or failure.

### Fields

- `run_id`: Stable local identifier for UI display and logs.
- `scenario`: Scenario key: `default`, `routing_cost`, `routing_latency`, `fallback`,
  `repeat_cache`, or `eval`.
- `prompt`: User-visible prompt text.
- `strategy_name`: Routing strategy selected for the run.
- `started_at`: Start timestamp.
- `completed_at`: Completion timestamp when available.
- `status`: `pending`, `streaming`, `succeeded`, `failed`, or `cancelled`.
- `streamed_text`: Accumulated visible response text.
- `error_message`: Human-readable failure reason when status is failed.
- `telemetry`: Associated `TelemetryEvidence`.
- `fallback_attempt`: Associated `FallbackAttempt` when fallback is exercised.

### Validation Rules

- `prompt` must be non-empty before a live inference request starts.
- `status=succeeded` requires a non-empty or explicitly empty final response state.
- `status=failed` requires `error_message`.
- Metadata not returned by OpenRouter/provider must be represented as unavailable, not guessed.

### State Transitions

```text
pending -> streaming -> succeeded
pending -> streaming -> failed
pending -> failed
streaming -> cancelled
```

## Entity: RoutingStrategy

Represents a named route selection mode for OpenRouter requests.

### Fields

- `name`: `default`, `cost`, `latency`, or `custom`.
- `description`: Reviewer-facing explanation of the strategy.
- `models`: Ordered OpenRouter model identifiers considered by the request.
- `provider_preferences`: Provider routing options such as order, allow/deny filters, price
  sorting, latency preference, and fallback allowance.
- `max_latency_seconds`: Optional local timeout threshold.
- `cost_guard`: Optional note or limit describing bounded demo spend.

### Validation Rules

- At least `default`, `cost`, and `latency` strategies must exist.
- Strategy descriptions must explain the tradeoff in reviewer-facing language.
- Strategy configuration must not imply guaranteed provider behavior that OpenRouter does not
  report.

## Entity: FallbackAttempt

Represents a reliability demonstration where a preferred route fails or times out and a
fallback route is attempted.

### Fields

- `primary_strategy`: Strategy/model/provider attempted first.
- `primary_status`: `failed`, `timed_out`, or `unavailable`.
- `primary_error`: Visible failure evidence.
- `fallback_strategy`: Strategy/model/provider attempted after primary failure.
- `fallback_status`: `not_attempted`, `succeeded`, or `failed`.
- `final_error`: Failure reason if fallback also fails.

### Validation Rules

- A fallback scenario must preserve primary failure evidence even when fallback succeeds.
- A deterministic failure trigger must be clearly labeled if used.

## Entity: TelemetryEvidence

Represents normalized observable data for a run.

### Fields

- `model`: Reported model identifier or unavailable.
- `provider`: Reported provider identifier or unavailable.
- `latency_ms`: Observed local latency.
- `prompt_tokens`: Reported prompt tokens or unavailable.
- `completion_tokens`: Reported completion tokens or unavailable.
- `total_tokens`: Reported total tokens or unavailable.
- `cost_usd`: Reported or calculated cost when source data supports it; otherwise unavailable.
- `cache_status`: Reported cache hit/miss/status or unavailable.
- `repeat_observation`: Observed repeat-run latency/cost comparison when cache metadata is unavailable.
- `fallback_used`: Boolean.
- `trace_status`: `enabled`, `disabled`, or `failed`.
- `trace_url`: Link when Langfuse tracing succeeds.

### Validation Rules

- Unavailable provider metadata must remain distinguishable from zero values.
- `trace_url` is present only when tracing succeeds.
- Cost values must include the source or be marked unavailable.

## Entity: EvalCase

Represents one deterministic eval item.

### Fields

- `case_id`: Stable identifier.
- `name`: Human-readable label.
- `prompt`: Eval prompt.
- `expected_terms`: Terms or criteria required for pass.
- `forbidden_terms`: Optional terms that fail the case.
- `scoring_notes`: Reviewer-facing scoring explanation.

### Validation Rules

- Three to five eval cases are required for the first shippable demo.
- Each case must have deterministic scoring criteria.
- Cases should be small enough to keep run cost predictable.

## Entity: EvalResult

Represents the scored output for one eval case under one route/model choice.

### Fields

- `case_id`: Eval case scored.
- `run_id`: Inference run that produced the output.
- `passed`: Boolean deterministic result.
- `score_reason`: Short explanation of pass/fail.
- `telemetry`: Associated telemetry evidence.

### Validation Rules

- Every eval result must include pass/fail and score reason.
- Eval result telemetry follows the same unavailable-metadata rules as live runs.
