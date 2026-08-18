# Phase 2: Streaming Inference Evidence

**Source intent:** `.planning/ROADMAP.md` Phase 2 + `.planning/REQUIREMENTS.md` INF-01..INF-06
**Phase goal:** User can submit a prompt through the UI and watch an OpenRouter chat completion stream back with basic request evidence (strategy, model/provider, latency, status, tokens, cost when available).
**Phase success criteria:**

1. User can submit a prompt through the UI and receive a live OpenRouter response.
2. Response text appears progressively while the request streams.
3. Completed run shows strategy, model/provider when available, latency, and success/failure state.
4. Token and cost fields display values only when available and otherwise show "Unavailable from selected route/provider."

**Decomposition rule applied:** Vertical MVP (per `.planning/ROADMAP.md` Phase 2 `**Mode:** mvp`). Backend pieces ship together as one PR because the UI cannot be exercised without all of them; UI integration ships as a second PR.

**Out of scope for Phase 2 (do not add):** routing-strategy selection UI beyond the Default, fallback scenarios, repeat/cache telemetry, Langfuse traces, eval execution, run-history comparison beyond a single-row append. These belong to later phases per `.planning/REQUIREMENTS.md`.

---

## PR-1: Phase 2 Streaming Backend

**Atomicity rationale:** client, models, run history, and routing are atomic together — the UI integration in PR-2 cannot start, and backend tests cannot exercise meaningful behavior, until all of them exist. Splitting them into separate PRs would leave each PR broken in isolation.

### Task 1.1 — Direct OpenRouter streaming client

- **Purpose:** Replace the Phase 1 `client.py` stub with a real httpx-based streamer against `https://openrouter.ai/api/v1/chat/completions` (`stream: true`). Surfaces partial text deltas and a final structured result with usage/metadata.
- **Dependencies:** `src/openrouter_demo/config.py` (for `OPENROUTER_API_KEY`), `httpx` (already in `pyproject.toml`).
- **PR boundary:** PR-1 (with Tasks 1.2, 1.3, 1.4, 1.5).
- **Acceptance criteria:**
  - `src/openrouter_demo/client.py` defines `stream_chat_completion(prompt: str, *, model: str, strategy: RoutingStrategy, api_key: str, http_client: httpx.AsyncClient | None = None) -> StreamedRun` (or equivalent shape — single async function returning an async iterator of `StreamChunk`s plus a final `StreamedResult`).
  - Function builds a JSON request body with `{"model": ..., "messages": [...], "stream": true}` and sends it to `https://openrouter.ai/api/v1/chat/completions` via `httpx.AsyncClient`.
  - Function sends `Authorization: Bearer <api_key>` and `Content-Type: application/json` headers.
  - Function parses SSE `data:` lines, concatenates `choices[0].delta.content` fragments, and yields each fragment as a chunk.
  - The final chunk (or a non-streaming fallback if `stream: false` is ever used) yields a `StreamedResult` containing: `text` (full concatenated text), `model` (reported model id, or `UNAVAILABLE`), `provider` (from `openrouter_metadata` if present, else `UNAVAILABLE`), `prompt_tokens`, `completion_tokens`, `total_tokens` (each `int | Unavailable`), `cost_usd` (`float | Unavailable`).
  - Function raises a typed exception (e.g. `OpenRouterHTTPError`, `OpenRouterAuthError`, `OpenRouterTimeoutError`) on HTTP/auth/timeout failures and preserves any partial text received before failure in the exception.
  - Function does **not** hide missing metadata: every absent field is `UNAVAILABLE`, never `0` or `0.0`.
- **Relevant files / components:**
  - `src/openrouter_demo/client.py` (replace stub)
  - `src/openrouter_demo/models.py` (add `StreamChunk`, `StreamedResult`; depends on Task 1.2)
  - `src/openrouter_demo/routing.py` (consume `RoutingStrategy`; depends on Task 1.4)
  - `pyproject.toml` (no new deps; `httpx` already declared)

### Task 1.2 — Typed run and telemetry models

- **Purpose:** Add the Phase 2 dataclasses (`InferenceRun`, `TelemetryEvidence`, run `Status` enum) plus the streaming types `StreamChunk` / `StreamedResult` consumed by the client and UI. Keeps Phase 1 `UNAVAILABLE` sentinel as the only way to represent missing data.
- **Dependencies:** None (extends `models.py` which already exports `UNAVAILABLE`).
- **PR boundary:** PR-1.
- **Acceptance criteria:**
  - `src/openrouter_demo/models.py` adds (per `docs/specs/data-model.md`):
    - `class Status(StrEnum): PENDING | STREAMING | SUCCEEDED | FAILED | CANCELLED`
    - `@dataclass(frozen=True) InferenceRun(run_id: str, prompt: str, strategy_name: str, started_at: datetime, completed_at: datetime | None, status: Status, streamed_text: str, error_message: str | None, telemetry: TelemetryEvidence | None)`
    - `@dataclass(frozen=True) TelemetryEvidence(model: str | Unavailable, provider: str | Unavailable, latency_ms: int, prompt_tokens: int | Unavailable, completion_tokens: int | Unavailable, total_tokens: int | Unavailable, cost_usd: float | Unavailable)`
    - `@dataclass(frozen=True) StreamChunk(text_delta: str)`
    - `@dataclass(frozen=True) StreamedResult(text: str, model: str | Unavailable, provider: str | Unavailable, prompt_tokens: int | Unavailable, completion_tokens: int | Unavailable, total_tokens: int | Unavailable, cost_usd: float | Unavailable, latency_ms: int)`
  - All absent fields use the existing `UNAVAILABLE` sentinel; no field defaults to `0` or `""`.
  - `TelemetryEvidence` exposes `__bool__`-friendly truth behavior on `UNAVAILABLE` already inherited from Phase 1.
- **Relevant files / components:**
  - `src/openrouter_demo/models.py` (extend)

### Task 1.3 — In-memory run history store

- **Purpose:** Hold completed `InferenceRun`s in a process-local list so the run-history panel (PR-2) can render rows. No persistence, no thread safety beyond NiceGUI's single-event-loop constraint.
- **Dependencies:** Task 1.2 (`InferenceRun`).
- **PR boundary:** PR-1.
- **Acceptance criteria:**
  - Add a small `RunHistory` class (in `src/openrouter_demo/scenarios.py` since `scenarios.py` already owns orchestration stubs, or a new `src/openrouter_demo/history.py` if cleaner — implementer's discretion, prefer reusing `scenarios.py` if it fits naturally) with `append(run: InferenceRun) -> None` and `all() -> list[InferenceRun]`.
  - Store is bounded by a sensible default (e.g. last 50 runs); older runs are dropped on append.
  - `RunHistory` is a plain class instance shared by the UI through `app.py` wiring; no module-level globals.
  - History never raises on append, never mutates a stored run (frozen dataclass enforces this).
- **Relevant files / components:**
  - `src/openrouter_demo/scenarios.py` (extend) or `src/openrouter_demo/history.py` (new — implementer's discretion)
  - `app.py` (one-line wiring of the shared instance — implementer can defer the wiring line itself to PR-2 if simpler)

### Task 1.4 — Default routing strategy

- **Purpose:** Add the minimum `RoutingStrategy` definition Phase 2 needs: at least one named strategy with a description and OpenRouter request payload. Phase 3 will add cost/latency/custom; do not introduce them here.
- **Dependencies:** None.
- **PR boundary:** PR-1.
- **Acceptance criteria:**
  - `src/openrouter_demo/routing.py` adds:
    - `@dataclass(frozen=True) RoutingStrategy(name: StrategyName, description: str, model: str, provider_preferences: dict[str, object] | None)`
    - `DEFAULT_STRATEGY = RoutingStrategy(name="default", description="Balanced route for general quality and availability.", model="openai/gpt-4o-mini", provider_preferences=None)` — exact model id chosen by the implementer from a small, currently-available OpenRouter model, with a docstring noting the choice is replaceable.
  - `StrategyName` literal type and `ROUTING_STRATEGY_LABELS` dict from Phase 1 remain unchanged.
  - Function `strategy_payload(strategy: RoutingStrategy) -> dict[str, object]` returns the JSON body fragment (currently just `{"model": strategy.model}`; `provider` is not included in Phase 2 because we have no provider preferences — keeps the request minimal and inspectable).
- **Relevant files / components:**
  - `src/openrouter_demo/routing.py` (extend)

### Task 1.5 — Backend unit tests

- **Purpose:** Prove the streaming backend behaves correctly without a live OpenRouter call. Tests fail loudly if metadata is misrepresented as zero or if exceptions lose partial text.
- **Dependencies:** Tasks 1.1, 1.2, 1.3, 1.4.
- **PR boundary:** PR-1.
- **Acceptance criteria:**
  - `tests/test_client.py` uses `httpx.MockTransport` to feed canned SSE responses and asserts:
    - Concatenated `text` matches expected concatenation of `choices[0].delta.content` fragments.
    - Reported `model` is read from the final chunk's `model` field; missing → `UNAVAILABLE`.
    - Missing `usage` block → token fields are `UNAVAILABLE`.
    - HTTP 401 → raises `OpenRouterAuthError`; HTTP 429 → `OpenRouterHTTPError`; transport timeout → `OpenRouterTimeoutError`. (Test names and exception names are implementer's discretion as long as they are typed and exported.)
    - When a 500 occurs mid-stream, the raised exception exposes the partial `text` received before the failure.
  - `tests/test_models.py` asserts:
    - `InferenceRun(status=FAILED).error_message` validation (optional, but `error_message is None` when `status != FAILED`).
    - `TelemetryEvidence(...).prompt_tokens is UNAVAILABLE` when constructed with `UNAVAILABLE` (i.e. `bool(value)` is `False`).
  - `tests/test_routing.py` asserts:
    - `DEFAULT_STRATEGY.name == "default"` and `description` matches the screen-spec wording.
    - `strategy_payload(DEFAULT_STRATEGY)` returns `{"model": <expected>}` and no `provider` key.
  - `tests/test_history.py` (or whatever the implementer names it) asserts:
    - `append()` followed by `all()` round-trips.
    - Bounded history drops oldest entries.
  - All tests pass under `uv run pytest`; `uv run ruff check .` passes against the new and modified files.
- **Relevant files / components:**
  - `tests/test_client.py` (new)
  - `tests/test_models.py` (new)
  - `tests/test_routing.py` (new)
  - `tests/test_history.py` (new — or whichever file the implementer picks)

**Definition of done for PR-1:**

- `src/openrouter_demo/{client,models,routing,scenarios|history}.py` import cleanly and expose the public functions/classes named above.
- `uv run pytest` passes with the new test files included; `uv run ruff check .` passes.
- No file under `src/` still raises `PhaseNotImplementedError` for the responsibilities above.
- No token, cost, model, or provider value is ever coerced to `0` / `0.0` / `""` when the source data is missing.

---

## PR-2: Phase 2 UI Integration

**Atomicity rationale:** the streaming button, response panel, telemetry panel, and run-history row all change together — they share the same state object and cannot be exercised without each other. UI integration test (Task 2.2) is atomic with the wiring (Task 2.1).

### Task 2.1 — Wire Run Inference button to streaming backend

- **Purpose:** Replace the Phase 1 disabled button with an enabled, async-driven flow: click → prompt validation → start `stream_chat_completion` → progressive response text → terminal telemetry → row in run history. Honor the screen-spec labels and states.
- **Dependencies:** PR-1 (Tasks 1.1–1.5) must be merged.
- **PR boundary:** PR-2 (with Task 2.2).
- **Acceptance criteria:**
  - `src/openrouter_demo/ui.py` `build_app()` accepts the `RunHistory` instance and exposes a `Run Inference` button that is enabled when the prompt is non-whitespace and disabled while a run is in flight.
  - Clicking the button spawns an async task that calls `stream_chat_completion(...)` (Task 1.1) and updates UI state on every `StreamChunk` (append text) and on completion (status, telemetry, run-history row).
  - Streaming response panel shows:
    - Empty state: "Run an inference request to see streaming output."
    - Streaming state: "Streaming from OpenRouter..." with progressively appended text.
    - Success state: "Request completed successfully."
    - Failure state: "Request failed before fallback could complete." plus a visible error message. Partial text accumulated before failure is preserved, not cleared.
  - Telemetry panel shows the fields required by the screen spec — Status, Strategy (selected strategy name), Model (or "Unavailable from selected route/provider."), Provider (or unavailable copy), Latency (in ms), Tokens (or unavailable copy), Cost (or "Cost metadata was not returned for this route/provider.") — with `UNAVAILABLE` rendered through explicit copy, not the string `"unavailable"` or `0`.
  - Run history panel renders a single row per completed run with the columns defined in `docs/ux/screen-spec.md`; missing fields show the same unavailable copy as the telemetry panel.
  - Sample prompts from `docs/ux/screen-spec.md` (eventual consistency, summarize incident, classify ticket, extract action items) populate the prompt textarea when the "Sample prompt" selector is used.
  - Failure modes (auth, rate limit, timeout, provider unavailable) render the screen-spec error patterns verbatim when the client raises typed exceptions.
  - `build_app()` keeps Phase 1's behavior for the missing-API-key path (setup guidance shell) and Langfuse status badge untouched.
- **Relevant files / components:**
  - `src/openrouter_demo/ui.py` (rewrite `build_app` to consume `RunHistory` + streaming client)
  - `app.py` (instantiate `RunHistory` and pass to `build_app`)

### Task 2.2 — UI integration / smoke test

- **Purpose:** Prove the wired UI handles the happy path, missing-metadata path, and a mid-stream failure path end-to-end without launching a browser. This is the smoke check that replaces the Phase 1 non-live launch smoke.
- **Dependencies:** Task 2.1.
- **PR boundary:** PR-2.
- **Acceptance criteria:**
  - `tests/test_ui.py` uses `httpx.MockTransport` to feed (a) a successful SSE response with usage, (b) a successful SSE response without usage, and (c) a transport that aborts mid-stream. The test instantiates `RunHistory`, invokes the async UI handler directly (no `ui.run()`), and asserts:
    - History contains exactly one `InferenceRun` per test.
    - `InferenceRun.streamed_text` matches the concatenated fragments.
    - Telemetry fields are `UNAVAILABLE` in case (b).
    - In case (c), the recorded `InferenceRun.status == FAILED`, `error_message` is non-empty, and `streamed_text` contains the partial text received before the abort.
  - Test passes under `uv run pytest`; `uv run ruff check .` passes.
  - No live OpenRouter call is made by any test (assert this by inspecting `httpx.MockTransport` request count).
- **Relevant files / components:**
  - `tests/test_ui.py` (new)

**Definition of done for PR-2:**

- `uv run python app.py` launches the NiceGUI shell; clicking `Run Inference` on a non-empty prompt with a valid `OPENROUTER_API_KEY` returns streamed text and populates the telemetry panel + run history.
- `uv run pytest` passes (Phase 1 tests + PR-1 backend tests + PR-2 UI test).
- `uv run ruff check .` passes.
- The screen displays the screen-spec streaming/telemetry/empty-state copy verbatim when triggered.
- No fake metadata appears anywhere in the UI.

---

## Cross-PR invariants (both PRs must respect)

- **`UNAVAILABLE` is the only way to represent missing data.** No `None`, no `0`, no `""`, no `"unknown"`. UI copy must render `UNAVAILABLE` through the screen-spec unavailable strings.
- **No live OpenRouter call happens in any test.** `httpx.MockTransport` (or equivalent) only.
- **No FastAPI, no separate API service.** NiceGUI remains the local UI surface; FastAPI is an internal implementation detail only.
- **Strategy selection in Phase 2 UI is `default` only.** Cost/latency/custom/failure-simulation UI belongs to Phase 3 per `docs/ux/screen-spec.md`. The PR-1 backend should expose the `RoutingStrategy` type so Phase 3 can plug in without reshaping the client.
- **Langfuse is not wired in Phase 2.** Tracing stays visibly disabled per Phase 1 contract; Phase 4 owns Langfuse integration.

---

## Requirements traceability

| Req ID | Description (verbatim from `.planning/REQUIREMENTS.md`) | Covered by |
|---|---|---|
| INF-01 | User can enter or use a prompt and run a live OpenRouter chat completion. | PR-2 Task 2.1 |
| INF-02 | User can see response text appear progressively while the model streams. | PR-1 Task 1.1 (client emits `StreamChunk`) + PR-2 Task 2.1 (UI appends) |
| INF-03 | Completed run displays selected strategy and actual model/provider evidence when available. | PR-1 Tasks 1.2, 1.4 (types + strategy) + PR-2 Task 2.1 (telemetry panel) |
| INF-04 | Completed run displays observed latency and success/failure state. | PR-1 Task 1.2 (latency_ms, status) + PR-2 Task 2.1 (telemetry panel) |
| INF-05 | Completed run displays token and cost metadata when available. | PR-1 Task 1.1 (extract usage from final chunk) + PR-2 Task 2.1 (telemetry panel with unavailable copy) |
| INF-06 | UI clearly distinguishes unavailable metadata from zero values. | PR-1 Task 1.2 (`UNAVAILABLE` sentinel) + PR-2 Task 2.1 (screen-spec unavailable copy) |

All six requirements are covered without scope creep into later phases.