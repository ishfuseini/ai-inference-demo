# Feature Specification: OpenRouter Inference Lab

**Feature Branch**: `001-openrouter-inference-lab`

**Created**: 2026-08-18

**Status**: Draft

**Input**: User description: "@openrouter_demo_prd_pure_openrouter.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run a Streaming Inference Demo (Priority: P1)

As the candidate, I want to run a live inference prompt and show the streamed response with
request evidence so that an interviewer can see that the demo operates real model calls, not
a static mock.

**Why this priority**: A working streaming model call is the foundation for every later
routing, fallback, cost, observability, and eval scenario.

**Independent Test**: Can be tested by starting the local demo, entering a prompt, running
the default strategy, and observing progressive output plus completed request evidence.

**Acceptance Scenarios**:

1. **Given** the reviewer has supplied the required inference credential, **When** the
   candidate runs the default prompt scenario, **Then** the response appears progressively
   and the completed run shows model, provider, latency, token usage when available, cost
   when available, fallback status, cache or repeat status, and trace status.
2. **Given** a metadata field is unavailable from the inference provider, **When** the run
   completes, **Then** the demo labels that field unavailable instead of displaying invented
   or guessed values.
3. **Given** observability credentials are absent, **When** the candidate runs inference,
   **Then** the run still completes and tracing is clearly marked disabled.

---

### User Story 2 - Demonstrate Routing and Fallback (Priority: P2)

As the candidate, I want to switch between routing strategies and trigger a reproducible
fallback path so that an interviewer can inspect reliability tradeoffs and failure handling.

**Why this priority**: The interview goal is to prove production inference reasoning, and
routing plus fallback are the clearest evidence that the candidate can operate unreliable
upstream model paths.

**Independent Test**: Can be tested by running a routing strategy scenario and a fallback
scenario, then comparing the visible route selection, failed route, recovered route, and
telemetry for both runs.

**Acceptance Scenarios**:

1. **Given** multiple routing strategies are available, **When** the candidate selects a
   cost-oriented or latency-oriented strategy, **Then** the completed run identifies the
   selected strategy and the resulting model/provider evidence.
2. **Given** a reproducible failure or timeout trigger is selected, **When** the candidate
   runs the fallback scenario, **Then** the demo shows the attempted primary route, the
   failure reason or timeout state, the fallback route, and the final success or failure.
3. **Given** fallback recovery succeeds, **When** the interviewer inspects the result,
   **Then** the demo preserves failure visibility instead of hiding the failed attempt.

---

### User Story 3 - Compare Cost, Latency, Cache, and Quality (Priority: P3)

As the candidate, I want to run comparable workloads across model choices and a small eval
set so that an interviewer can see how quality, latency, reliability, and cost tradeoffs are
made with evidence.

**Why this priority**: The demo must show not only that calls work, but that model selection
can be evaluated and explained from observable outcomes.

**Independent Test**: Can be tested by running repeated prompts and the eval scenario, then
reviewing the displayed comparison of quality, latency, cost, model/provider, trace status,
and cache or repeat behavior.

**Acceptance Scenarios**:

1. **Given** the same or equivalent prompt is run under different strategies, **When** the
   runs complete, **Then** the demo presents comparable latency, token, cost, model/provider,
   and cache or repeat observations without declaring unsupported cache hits.
2. **Given** the eval scenario is run, **When** all cases finish, **Then** the output shows
   deterministic pass/fail scoring for three to five cases plus latency, cost, model/provider,
   and trace status per result.
3. **Given** optional richer judging is unavailable or disabled, **When** evals run, **Then**
   deterministic scoring remains sufficient to compare results.

---

### User Story 4 - Walk Through the Demo in an Interview (Priority: P4)

As the interviewer, I want a concise run guide, failure tree, and readable project story so
that I can understand the demo in 30 seconds, see the core behavior in five minutes, and ask
technical questions from evidence.

**Why this priority**: The artifact succeeds only if the interviewer can quickly understand
what is being demonstrated and inspect failure-handling decisions.

**Independent Test**: Can be tested by following the run guide from a clean checkout with the
required inference credential and completing the five-minute walkthrough.

**Acceptance Scenarios**:

1. **Given** the interviewer opens the repository, **When** they read the primary guide,
   **Then** they can understand that the demo proves routing, fallback, caching or repeat
   behavior, cost optimization, evals, and observability.
2. **Given** a run fails, **When** the candidate follows the failure tree, **Then** the guide
   covers client, credential, provider, routing, timeout, telemetry, and display failure
   classes.
3. **Given** the interviewer wants to inspect implementation scope, **When** they review the
   project, **Then** the demo is small enough to understand during a technical walkthrough
   and does not present a separate service or product architecture beyond the demo.

---

### Edge Cases

- Missing required inference credential prevents live runs and shows a clear setup message.
- Missing observability credentials disables tracing without blocking core inference.
- Provider metadata for token usage, cost, cache status, or provider identity may be absent;
  the demo labels absence explicitly.
- A real provider outage may not be reproducible on demand; the fallback scenario may use a
  clearly labeled deterministic failure trigger while preserving a real fallback path.
- A streaming response may end early, error mid-stream, or time out; the partial result and
  error state remain visible.
- Repeated prompts may not produce provider cache metadata; the demo reports observed repeat
  latency and cost without inventing cache claims.
- Eval cases may fail because of model output variance; deterministic scoring must show the
  criterion that passed or failed.
- Live runs can spend money; default workloads remain bounded and small enough for interview
  use.

## Scope Boundaries *(mandatory)*

- **Demo Capability Served**: Streaming, routing, fallback, cache/repeat behavior, cost and
  latency comparison, evals, observability, failure diagnosis, and five-minute interview
  walkthrough readiness.
- **In Scope**: A local interactive inference lab, visible telemetry per run, reproducible
  fallback demonstration, small deterministic eval set, optional trace linkage, concise run
  guide, and failure tree.
- **Out of Scope**: Authentication, multi-tenancy, high availability, production scale,
  database persistence, background job queues, a separate product API, a separate frontend
  application, Docker as a core requirement, a full eval platform, a golden-set pipeline,
  and broad UI polish unrelated to inference evidence.
- **Constitution Alignment**: The feature preserves direct OpenRouter value, keeps runtime
  evidence honest, bounds cost exposure, treats observability as optional but visible, and
  limits scope to a compact interview demo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The demo MUST allow a candidate to run a live streaming inference prompt and
  observe the response progressively.
- **FR-002**: The demo MUST show completed-run evidence including selected strategy,
  model/provider, latency, fallback status, success or failure state, trace status, token
  usage when available, cost when available, and cache or repeat status when available.
- **FR-003**: The demo MUST clearly mark unavailable metadata instead of substituting
  guessed, hard-coded, or fabricated values.
- **FR-004**: The demo MUST support at least three routing choices: default, cost-oriented,
  and latency-oriented.
- **FR-005**: The demo MUST provide a reproducible fallback scenario that shows the failed
  preferred route and the attempted fallback route.
- **FR-006**: The demo MUST keep core inference runs usable when optional observability
  credentials are absent and MUST visibly indicate tracing is disabled.
- **FR-007**: The demo MUST create traceable observability records for demo calls when
  observability credentials are configured.
- **FR-008**: The demo MUST include a repeat/cache scenario that reports observed repeat
  behavior and provider cache metadata only when available.
- **FR-009**: The demo MUST include three to five eval cases with deterministic pass/fail
  scoring.
- **FR-010**: Eval output MUST compare quality result, latency, cost when available,
  model/provider, and trace status for each evaluated run.
- **FR-011**: The demo MUST include setup guidance that lets a reviewer run the core demo
  with only the required inference credential and optional observability credentials.
- **FR-012**: The demo MUST document all required and optional environment variables without
  exposing secret values.
- **FR-013**: The demo MUST include a failure tree that helps explain credential, request,
  provider, routing, timeout, telemetry, and display failures.
- **FR-014**: The demo MUST remain scoped to an interview artifact and MUST NOT introduce
  production SaaS capabilities outside the stated scope boundaries.
- **FR-015**: The demo MUST include focused validation for response/error handling, routing
  configuration, and eval scoring.

### Key Entities *(include if feature involves data)*

- **Inference Run**: A single prompt execution, including prompt, selected strategy,
  streamed output, completion state, metadata availability, errors, and trace status.
- **Routing Strategy**: A named selection mode such as default, cost-oriented,
  latency-oriented, or custom preference, with the resulting route evidence visible to the
  reviewer.
- **Fallback Attempt**: The primary route attempt, failure or timeout evidence, fallback
  route attempt, and final result.
- **Telemetry Evidence**: Observable fields attached to a run, including latency, token
  usage, cost, provider/model, fallback status, cache or repeat status, and trace status.
- **Eval Case**: A prompt plus deterministic scoring criteria used to compare model choices.
- **Eval Result**: The scored output for one eval case, including pass/fail result, quality
  evidence, latency, cost when available, model/provider, and trace status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An interviewer can understand what the demo proves within 30 seconds of
  opening the project guide.
- **SC-002**: A candidate can complete the live demo sequence for streaming, routing,
  fallback, evals, and observability in five minutes or less after setup.
- **SC-003**: A reviewer can run the core demo from a clean checkout with one required
  inference credential and optional observability credentials in 10 minutes or less.
- **SC-004**: Each completed live run displays at least six evidence fields: model/provider,
  latency, fallback status, success or failure state, trace status, and token, cost, or cache
  information when available.
- **SC-005**: The fallback scenario visibly shows both the failed preferred route and the
  fallback route in 100% of fallback demo runs.
- **SC-006**: The eval scenario completes three to five cases and reports deterministic
  pass/fail results for 100% of cases.
- **SC-007**: The demo contains zero committed secrets and documents every required or
  optional credential used by the reviewer.
- **SC-008**: The project remains inspectable enough that the candidate can explain the core
  request, routing, telemetry, and eval surfaces during a 15-minute code walkthrough.

## Assumptions

- The primary users are a Forward Deployed Engineer interviewer and the candidate driving an
  interview walkthrough.
- The demo is local-first and does not need hosted deployment, authentication, persistent
  storage, or multiple users.
- Live inference requires the reviewer or candidate to provide a valid OpenRouter credential.
- Observability credentials are optional because the core inference demo must still run when
  tracing is unavailable.
- Default workloads use small, bounded prompts to keep cost predictable.
- Cache behavior depends on the selected route/provider and may be reported as unavailable
  when not exposed by the provider.
- The first shippable scope is the minimal six-capability demo; richer judging, diagrams,
  and additional polish are fast-follow work only if they strengthen the interview story.
