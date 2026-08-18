# Acceptance Criteria - OpenRouter Production Inference Lab

This document breaks the PRD acceptance criteria into implementation-focused categories.

## Demo-critical acceptance criteria

These determine whether the interview demo works.

- [ ] `uv sync` installs the project successfully.
- [ ] `uv run python app.py` launches the NiceGUI UI.
- [ ] A user can run a real streaming OpenRouter request.
- [ ] Streaming tokens appear progressively in the UI.
- [ ] The completed request displays actual model metadata where available.
- [ ] The completed request displays provider metadata where available.
- [ ] The completed request displays observed latency.
- [ ] The completed request displays token usage where available.
- [ ] The completed request displays cost metadata where available.
- [ ] The UI clearly distinguishes unavailable metadata from zero values.
- [ ] At least two routing strategies can be demonstrated using the same prompt.
- [ ] The UI makes the selected routing strategy visible before and after the run.
- [ ] The UI shows the actual route/model used, not only the requested strategy.
- [ ] At least one reproducible fallback scenario can be triggered.
- [ ] Fallback behavior shows both the failed primary attempt and the successful fallback attempt.
- [ ] Failure is visible to the user and not silently hidden.
- [ ] Repeat/cache behavior is reported honestly based on returned metadata or observed repeat latency/cost.
- [ ] The app never claims a cache hit unless cache metadata or route behavior supports that claim.
- [ ] Langfuse receives traces when credentials are configured.
- [ ] The app still works when Langfuse credentials are absent.
- [ ] When Langfuse is absent, the UI clearly says tracing is disabled.

## Eval acceptance criteria

These prove safe model selection.

- [ ] `make eval` or an equivalent `uv` command runs the eval set.
- [ ] Eval set includes at least 3 deterministic cases.
- [ ] Each eval case has a clear pass/fail rule.
- [ ] Eval output includes model/strategy used.
- [ ] Eval output includes pass/fail result.
- [ ] Eval output includes latency.
- [ ] Eval output includes token/cost metadata where available.
- [ ] Eval output includes Langfuse trace IDs when tracing is enabled.
- [ ] Eval summary supports comparison across at least two strategies or models.
- [ ] Eval output is understandable without reading the source code.

## UI/UX acceptance criteria

These determine whether the demo communicates well.

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

## Repository acceptance criteria

These prove engineering discipline.

- [ ] README explains the story, setup, env vars, and five-minute walkthrough.
- [ ] `.env.example` documents `OPENROUTER_API_KEY`.
- [ ] `.env.example` documents optional Langfuse variables.
- [ ] No secrets are committed.
- [ ] `client.py` owns OpenRouter request construction, streaming, errors, and metadata normalization.
- [ ] `routing.py` owns model/provider strategy definitions.
- [ ] `telemetry.py` owns Langfuse and normalized runtime metrics.
- [ ] `scenarios.py` owns deterministic demo scenarios.
- [ ] `evals.py` owns eval cases and scoring.
- [ ] UI code does not embed business/inference logic.
- [ ] Core response/error handling has focused tests.
- [ ] Routing configuration has focused tests.
- [ ] Eval scoring has focused tests.
- [ ] `uv run pytest` passes.
- [ ] `uv run ruff check .` passes.
- [ ] The repository does not present FastAPI as a separate architecture layer.
- [ ] A reviewer can run the core demo with only `OPENROUTER_API_KEY`.
