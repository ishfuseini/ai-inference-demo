---
phase: 02-streaming-inference-evidence
status: complete
mode: operate
sources:
  - docs/ux/screen-spec.md
  - docs/ux/ui-ux-plan.md
  - docs/ux/demo-script.md
  - docs/tasks/phase-2-streaming-inference.md
  - .planning/REQUIREMENTS.md
  - src/openrouter_demo/ui.py
  - app.py
created: 2026-08-19
---

# Phase 02 UI-SPEC: Streaming Inference Evidence

## Scope

Phase 02 turns the existing Phase 1 NiceGUI shell into a default-route streaming inference console. The UI remains a single-screen inference operations console, not a chatbot.

In scope:

- Prompt textarea and sample prompt action/selector.
- `Run Inference` enabled only when prompt text is non-whitespace and `OPENROUTER_API_KEY` is configured.
- Default strategy only, shown as `Default` with the description `Balanced route for general quality and availability.`
- Progressive streaming response panel.
- Telemetry panel with status, strategy, model, provider, latency, tokens, and cost.
- Run-history table with one row per completed or failed run.
- Existing missing-key setup guidance and Langfuse disabled state preserved.

Out of scope:

- Cost optimized, latency optimized, custom route controls.
- Fallback simulation toggle and fallback success UI beyond the reserved copy.
- Cache/repeat claims.
- Langfuse trace links or trace creation.
- Eval execution dashboard.
- Separate frontend or FastAPI product API.

## Layout contract

Use a compact one-page NiceGUI layout:

1. Header: title, subtitle, optional supporting line.
2. Credential/status row: OpenRouter readiness and Langfuse tracing readiness.
3. Request card: prompt textarea, sample prompt control, default strategy summary, `Run Inference` button.
4. Two-column evidence area on medium+ widths: streaming response and telemetry.
5. Run history card below.
6. Future operation panels remain visibly out-of-scope for fallback/cache/evals.

## Required copy

- Title: `OpenRouter Production Inference Lab`
- Subtitle: `Route, observe, recover, and evaluate model calls.`
- Supporting line: `A model call is easy. Operating inference is the real problem.`
- Prompt label: `Prompt`
- Prompt placeholder: `Ask a production-style question, classification task, or summarization task...`
- Primary button: `Run Inference`
- Empty response: `Run an inference request to see streaming output.`
- Streaming state: `Streaming from OpenRouter...`
- Success state: `Request completed successfully.`
- Failure state: `Request failed before fallback could complete.`
- Model/provider unavailable: `Unavailable from selected route/provider.`
- Cost unavailable: `Cost metadata was not returned for this route/provider.`
- Tracing disabled: `Langfuse tracing disabled. Configure Langfuse credentials to enable trace links.`

## State inventory

| State | Required behavior |
|---|---|
| Missing OpenRouter key | Preserve Phase 1 setup card: `Set OPENROUTER_API_KEY in your shell, then restart the app.` `Run Inference` is disabled. |
| Empty prompt | `Run Inference` is disabled or handler returns without starting a request. |
| Ready idle | Prompt can be edited; sample prompt can populate textarea; response empty state is visible. |
| Streaming | Button disabled; response text appends progressively; telemetry status shows streaming. |
| Success | Response status shows success; telemetry fields update; history gets one row. |
| Metadata unavailable | UI renders explicit unavailable copy, never `0`, empty string, or raw sentinel text. |
| Failure with partial text | Partial text remains visible; failure copy and debugging error message are visible; history records failure. |
| Langfuse absent | UI says tracing is disabled/optional and does not block inference. |

## Accessibility and interaction

- The button label must remain text-visible as `Run Inference`; avoid icon-only actions.
- Prompt control must be keyboard reachable and should not require mouse-only interaction.
- Disabled/in-progress state must be visible through button disabled state and status copy, not color alone.
- Telemetry labels must be text labels, not only visual positioning.
- Preserve high contrast for warning/setup cards and status text.

## UI Considerations

- statement: `INF-01: A non-empty prompt with configured OPENROUTER_API_KEY exposes an enabled Run Inference path from the NiceGUI UI.`
  status: resolved
  verification: explicit
- statement: `INF-02: Streaming response text appears progressively in the response panel while the request is active.`
  status: resolved
  verification: explicit
- statement: `INF-03: Completed run shows selected strategy and actual model/provider evidence when available, using unavailable copy when absent.`
  status: resolved
  verification: explicit
- statement: `INF-04: Completed run shows observed latency and success/failure state.`
  status: resolved
  verification: explicit
- statement: `INF-05: Token and cost metadata render only when available; absent cost uses the required cost-unavailable copy.`
  status: resolved
  verification: explicit
- statement: `INF-06: UI distinguishes unavailable metadata from zero values and never renders raw sentinel internals as user-facing evidence.`
  status: resolved
  verification: explicit
- statement: `Phase 02 UI must not add Phase 3+ controls for cost/latency/custom routes, fallback simulation, cache/repeat, Langfuse traces, or eval execution.`
  status: resolved
  verification: explicit

## Files affected

- `src/openrouter_demo/ui.py`: state handler, formatting helpers, NiceGUI layout, streaming/telemetry/history rendering.
- `app.py`: instantiate `RunHistory` and pass it to `build_app`.
- `tests/test_ui.py`: mocked stream/UI-state tests without `ui.run()` and without live OpenRouter.
