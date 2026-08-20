# Roadmap: OpenRouter Production Inference Lab

**Created:** 2026-08-18
**Mode:** Vertical MVP
**Granularity:** Standard

## Phases

- [x] **Phase 1: Runnable Skeleton and Config** - Reviewer can install, configure, and launch the local app shell.
- [x] **Phase 2: Streaming Inference Evidence** - User can run a live streaming OpenRouter request with basic telemetry.
- [x] **Phase 3: Routing and Fallback Demo** - User can compare routing strategies and inspect reproducible fallback behavior.
- [x] **Phase 4: Telemetry, Repeat, and Observability** - User can compare runs with honest metadata, repeat/cache observations, and optional Langfuse traces.
- [x] **Phase 5: Deterministic Evals** - User can run small evals and compare model/strategy quality with telemetry evidence. (completed 2026-08-20)
- [ ] **Phase 6: Interview Walkthrough and Quality Gates** - Reviewer can follow docs and trust focused tests/lint checks.

## Phase Details

### Phase 1: Runnable Skeleton and Config

**Goal**: Reviewer can install dependencies, configure credentials, and launch a local NiceGUI shell without secrets in git.
**Mode:** mvp
**Depends on**: Nothing
**Requirements**: SETUP-01, SETUP-02, SETUP-03, SETUP-04, SETUP-05, SETUP-06
**Success Criteria** (what must be TRUE):

  1. Reviewer can run `uv sync` and create the project environment.
  2. Reviewer can run `uv run python app.py` and reach a local NiceGUI page.
  3. Missing `OPENROUTER_API_KEY` produces clear setup guidance instead of an attempted live call.
  4. Missing Langfuse credentials do not block app launch.
  5. Source layout separates UI, client, routing, scenarios, telemetry, evals, and typed models.

**Plans**: 3 plans
Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Verify package legitimacy gate before dependency resolution.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Create install, env config, setup docs, and NiceGUI launch tracer.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-03-PLAN.md — Add importable package boundaries and non-live guard tests.

**UI hint**: yes

### Phase 2: Streaming Inference Evidence

**Goal**: User can run a live OpenRouter prompt and watch response text stream with basic request evidence.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: INF-01, INF-02, INF-03, INF-04, INF-05, INF-06
**Success Criteria** (what must be TRUE):

  1. User can submit a prompt through the UI and receive a live OpenRouter response.
  2. Response text appears progressively while the request streams.
  3. Completed run shows strategy, model/provider when available, latency, and success/failure state.
  4. Token and cost fields display values only when available and otherwise show unavailable.

**Plans**: 2 PRs (see `docs/tasks/phase-2-streaming-inference.md`)
Plans:
**PR-1** (merged)

- [x] Streaming backend: client, models, routing, history, backend tests

**PR-2** (merged)

- [x] UI integration: wire Run Inference button, streaming panel, telemetry panel, run history row, UI smoke test

**UI hint**: yes

### Phase 3: Routing and Fallback Demo

**Goal**: User can compare strategy tradeoffs and trigger a fallback path that preserves primary failure evidence.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: ROUTE-01, ROUTE-02, ROUTE-03, ROUTE-04, ROUTE-05, ROUTE-06
**Success Criteria** (what must be TRUE):

  1. User can choose default, cost-oriented, and latency-oriented strategies before running.
  2. UI explains each strategy in reviewer-facing tradeoff language.
  3. Completed runs show selected strategy and actual returned route/model evidence.
  4. Fallback scenario shows primary attempt, failure or timeout reason, fallback route, and final result.
  5. A successful fallback never hides the failed primary attempt.

**Plans**: 2 plans
Plans:
**Wave 1**

- [x] 03-01-PLAN.md — Strategy selection vertical slice: routing strategies, model types, UI selector, strategy payloads

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-02-PLAN.md — Fallback scenario vertical slice: two-attempt orchestration, UI toggle, fallback evidence rendering

**UI hint**: yes

### Phase 4: Telemetry, Repeat, and Observability

**Goal**: User can compare recent runs using normalized metadata, repeat/cache observations, and optional Langfuse traces.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: OBS-01, OBS-02, OBS-03, OBS-04, OBS-05, OBS-06, OBS-07
**Success Criteria** (what must be TRUE):

  1. Every run has normalized telemetry fields for model/provider, latency, tokens, cost, fallback, cache/repeat, and trace state.
  2. Router metadata is requested where useful and its absence is handled explicitly.
  3. Repeat/cache scenario reports cache metadata only when provider data supports it.
  4. If cache metadata is absent, repeat/cache scenario shows observed repeat latency and cost instead.
  5. Langfuse traces are created when configured and tracing disabled is visible when not configured.
  6. Recent run history supports comparison from the main UI.

**Plans**: 3 plans
Plans:
**Wave 1**

- [x] 04-01-PLAN.md — Normalized telemetry vertical slice: cache/trace fields, metadata header, conditional Langfuse.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 04-02-PLAN.md — Repeat/cache scenario slice: two-run observation with cache honesty + Repeat UI action.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 04-03-PLAN.md — Persistence round-trip + history comparison slice.

**UI hint**: yes

### Phase 5: Deterministic Evals

**Goal**: User can run three to five deterministic eval cases and compare quality, latency, cost, model/provider, and trace state.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: EVAL-01, EVAL-02, EVAL-03, EVAL-04, EVAL-05, EVAL-06
**Success Criteria** (what must be TRUE):

  1. Eval command or scenario runs three to five deterministic cases.
  2. Every eval case reports pass/fail and a score reason.
  3. Eval output includes model or strategy, latency, trace state, and token/cost metadata when available.
  4. Eval summary supports comparison across at least two strategies or models.
  5. Langfuse trace IDs or disabled trace state are reported consistently.

**Plans**: 1/1 plans executed
Plans:
**Wave 1**

- [x] 05-01-PLAN.md — Deterministic eval CLI: 5-case JSON, keyword scoring, honest telemetry, strategy/model comparison, and guard-test updates.

**UI hint**: yes

### Phase 6: Interview Walkthrough and Quality Gates

**Goal**: Reviewer can follow the project story, debug failures, and verify focused quality gates.
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: DOC-01, DOC-02, DOC-03, DOC-04, DOC-05, DOC-06, DOC-07, DOC-08
**Success Criteria** (what must be TRUE):

  1. README explains the story, setup, env vars, and five-minute walkthrough.
  2. Architecture guide and failure tree match the implemented behavior.
  3. UI communicates inference operation rather than generic chatbot framing.
  4. Focused tests cover response/error handling, routing config, telemetry normalization, and eval scoring.
  5. `uv run pytest` and `uv run ruff check .` pass.
  6. Reviewer can run the core demo with only `OPENROUTER_API_KEY`.

**Plans**: 3 plans
Plans:
**Wave 1**

- [x] 06-01-PLAN.md — Docs slice: create docs/architecture.md, rewrite README.md, move failure tree to docs/failure-tree.md, fix quickstart, and pin with tests/test_docs.py.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 06-02-PLAN.md — Guard-tests slice: DOC-04 UI-framing guard in tests/test_ui.py and DOC-05 focused-coverage guard in tests/test_docs.py.

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 06-03-PLAN.md — Quality-gate confirmation: uv run pytest (DOC-06), uv run ruff check . (DOC-07), and single-credential demo confirmation (DOC-08).

**UI hint**: yes

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Runnable Skeleton and Config | 3/3 | Complete    | 2026-08-18 |
| 2. Streaming Inference Evidence | 2/2 | Complete    | 2026-08-19 |
| 3. Routing and Fallback Demo | 2/2 | Complete | 2026-08-19 |
| 4. Telemetry, Repeat, and Observability | 3/3 | Complete | 2026-08-19 |
| 5. Deterministic Evals | 1/1 | Complete    | 2026-08-20 |
| 6. Interview Walkthrough and Quality Gates | 2/3 | In progress | - |

## Coverage

| Phase | Requirements |
|-------|--------------|
| Phase 1 | SETUP-01, SETUP-02, SETUP-03, SETUP-04, SETUP-05, SETUP-06 |
| Phase 2 | INF-01, INF-02, INF-03, INF-04, INF-05, INF-06 |
| Phase 3 | ROUTE-01, ROUTE-02, ROUTE-03, ROUTE-04, ROUTE-05, ROUTE-06 |
| Phase 4 | OBS-01, OBS-02, OBS-03, OBS-04, OBS-05, OBS-06, OBS-07 |
| Phase 5 | EVAL-01, EVAL-02, EVAL-03, EVAL-04, EVAL-05, EVAL-06 |
| Phase 6 | DOC-01, DOC-02, DOC-03, DOC-04, DOC-05, DOC-06, DOC-07, DOC-08 |

**Coverage:** 39/39 v1 requirements mapped

---
*Roadmap created: 2026-08-18*
