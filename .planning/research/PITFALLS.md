# Domain Pitfalls

**Domain:** Production inference demo
**Researched:** 2026-08-18
**Overall confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Claiming Metadata That Was Not Returned

**What goes wrong:** The UI displays zeros or hard-coded values for token usage, cost, provider, or cache state.

**Why it happens:** Provider responses and router metadata vary by route, endpoint, stream state, and cache behavior.

**Consequences:** The interview demo becomes less credible because it overclaims production evidence.

**Prevention:** Use typed unavailable states and render "unavailable" distinctly from numeric zero.

**Detection:** Tests should cover missing usage, cost, provider, and cache fields.

### Pitfall 2: Silent or Hidden Fallback

**What goes wrong:** A fallback succeeds, but the UI only shows a successful final answer.

**Why it happens:** Error handling collapses multiple attempts into one final status.

**Consequences:** The reliability story disappears, and the candidate cannot debug the failed primary route.

**Prevention:** Model fallback attempts explicitly and show primary failure plus fallback result.

**Detection:** Fallback scenario acceptance test must assert both attempts are visible.

### Pitfall 3: Blocking Streaming UI Updates

**What goes wrong:** The app waits until the request finishes before updating the UI, or the UI freezes during network I/O.

**Why it happens:** Synchronous HTTP or blocking work runs inside an async UI handler.

**Consequences:** The demo fails its first and most visible promise: progressive streaming.

**Prevention:** Use async HTTP streaming and NiceGUI async/background-task patterns.

**Detection:** Manual demo should show progressive text; tests should cover stream parser events.

### Pitfall 4: Making Langfuse Required

**What goes wrong:** Missing Langfuse credentials prevent the OpenRouter demo from running.

**Why it happens:** Tracing setup is treated as core configuration rather than optional observability.

**Consequences:** Reviewer setup becomes fragile and the single required credential promise breaks.

**Prevention:** Detect Langfuse credentials separately and render tracing disabled when absent.

**Detection:** Config tests should verify core run readiness with only `OPENROUTER_API_KEY`.

## Moderate Pitfalls

### Pitfall 1: Over-Constrained Routing

**What goes wrong:** Provider allow/deny/order settings prevent fallback or make a route unavailable.

**Prevention:** Keep default strategies simple; label constrained custom/fallback demos clearly.

### Pitfall 2: Eval Flakiness

**What goes wrong:** The eval set depends on subjective judgment or large prompts.

**Prevention:** Use small deterministic cases with expected and forbidden terms.

### Pitfall 3: Interview Docs Drift From Code

**What goes wrong:** README, quickstart, and failure tree claim behavior that implementation does not provide.

**Prevention:** Update docs in the phase that implements the related behavior and run the documented commands.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Setup | Missing credential behavior is unclear | Add `.env.example` and visible setup state early. |
| Streaming | Mid-stream error is lost | Preserve partial output and terminal error event. |
| Routing/fallback | Fallback path is not reproducible | Include a clearly labeled deterministic trigger. |
| Telemetry | Cache claims are unsupported | Report provider metadata only when present; otherwise show repeat observation. |
| Evals | Scores are not explainable | Include pass/fail reason for every eval result. |
| Docs/tests | Walkthrough diverges from commands | Verify quickstart commands during final phase. |

## Sources

- `docs/specs/acceptance-criteria.md`
- `docs/specs/failure-tree.md`
- OpenRouter Streaming: https://openrouter.ai/docs/api/reference/streaming
- OpenRouter Provider Routing: https://openrouter.ai/docs/guides/routing/provider-selection
- OpenRouter Router Metadata: https://openrouter.ai/docs/guides/features/router-metadata
- NiceGUI docs via Context7 `/zauberzeug/nicegui`
