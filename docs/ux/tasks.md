# Tasks: OpenRouter Inference Lab

**Input**: Design documents from `/specs/001-openrouter-inference-lab/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Focused pytest tasks are included for changed core response parsing, routing, fallback, telemetry, and eval scoring per constitution.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single Python project**: `src/openrouter_demo/`, `tests/`, `evals/`, `docs/` at repository root
- **Feature docs**: `specs/001-openrouter-inference-lab/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the repository shape, dependency metadata, and local run surfaces.

- [ ] T001 Create project package directories and placeholder files in src/openrouter_demo/, tests/, evals/, docs/, and app.py
- [ ] T002 Create uv project metadata with Python 3.12, NiceGUI, Langfuse, httpx, pytest, and Ruff in pyproject.toml
- [ ] T003 [P] Create required and optional credential examples in .env.example
- [ ] T004 [P] Create uv-backed helper targets in Makefile
- [ ] T005 [P] Create package marker and exports in src/openrouter_demo/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core types, configuration, routing, telemetry, and scenario seams required before user-story work.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T006 Define InferenceRun, RoutingStrategy, FallbackAttempt, TelemetryEvidence, EvalCase, and EvalResult models in src/openrouter_demo/models.py
- [ ] T007 Implement environment configuration loading for OpenRouter and optional Langfuse in src/openrouter_demo/config.py
- [ ] T008 Implement default, cost, latency, and custom routing strategy definitions in src/openrouter_demo/routing.py
- [ ] T009 Implement unavailable-metadata and trace-status normalization helpers in src/openrouter_demo/telemetry.py
- [ ] T010 Implement OpenRouter request body construction, timeout settings, and streaming parser seams in src/openrouter_demo/client.py
- [ ] T011 Implement scenario orchestration entry points for normal, fallback, repeat_cache, and eval scenarios in src/openrouter_demo/scenarios.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel after dependencies are respected.

---

## Phase 3: User Story 1 - Run a Streaming Inference Demo (Priority: P1) MVP

**Goal**: A candidate can run a live prompt, see streamed text, and inspect honest completed-run evidence.

**Independent Test**: Start the local UI, run the default strategy with a prompt, and observe progressive output plus model/provider, latency, trace status, fallback status, and unavailable metadata labels.

### Tests for User Story 1

> Write these tests first and ensure they fail before implementation.

- [ ] T012 [US1] Add response streaming, unavailable metadata, and enabled/disabled Langfuse tracing tests in tests/test_response_handling.py

### Implementation for User Story 1

- [ ] T013 [US1] Implement live OpenRouter streaming request execution and chunk parsing in src/openrouter_demo/client.py
- [ ] T014 [US1] Implement telemetry capture plus optional Langfuse trace/generation creation and trace URL/status propagation in src/openrouter_demo/telemetry.py
- [ ] T015 [US1] Implement normal streaming scenario orchestration in src/openrouter_demo/scenarios.py
- [ ] T016 [US1] Implement NiceGUI prompt input, strategy selector, run button, streaming output, and telemetry panel in src/openrouter_demo/ui.py
- [ ] T017 [US1] Wire app entry point to load config, register UI, and start the local app in app.py

**Checkpoint**: User Story 1 is independently runnable with `uv run python app.py` and the default strategy.

---

## Phase 4: User Story 2 - Demonstrate Routing and Fallback (Priority: P2)

**Goal**: A candidate can switch routing strategies and trigger a reproducible fallback path with visible primary failure evidence.

**Independent Test**: Run cost and latency strategies, then trigger fallback and verify preferred route, failure reason, fallback route, final state, and telemetry remain visible.

### Tests for User Story 2

> Write these tests first and ensure they fail before implementation.

- [ ] T018 [US2] Add routing strategy and fallback preservation tests in tests/test_routing_config.py

### Implementation for User Story 2

- [ ] T019 [US2] Implement provider routing request fields for cost and latency strategies in src/openrouter_demo/routing.py
- [ ] T020 [US2] Implement deterministic fallback trigger and fallback attempt recording in src/openrouter_demo/scenarios.py
- [ ] T021 [US2] Implement fallback error classification and recovered-route telemetry in src/openrouter_demo/client.py
- [ ] T022 [US2] Display routing strategy evidence, primary failure evidence, fallback route, and final state in src/openrouter_demo/ui.py

**Checkpoint**: User Stories 1 and 2 both work independently through the local UI.

---

## Phase 5: User Story 3 - Compare Cost, Latency, Cache, and Quality (Priority: P3)

**Goal**: A candidate can compare repeat/cache observations and run a small deterministic eval set with quality, latency, cost, model/provider, and trace evidence.

**Independent Test**: Run repeat/cache scenario and `uv run python -m openrouter_demo.evals`, then inspect cache-or-repeat evidence and deterministic pass/fail eval output for three to five cases.

### Tests for User Story 3

> Write these tests first and ensure they fail before implementation.

- [ ] T023 [US3] Add deterministic eval scoring tests in tests/test_eval_scoring.py
- [ ] T024 [US3] Add repeat/cache telemetry normalization tests in tests/test_response_handling.py

### Implementation for User Story 3

- [ ] T025 [P] [US3] Create three to five deterministic eval cases in evals/cases.json
- [ ] T026 [US3] Implement deterministic eval loading, scoring, and command output in src/openrouter_demo/evals.py
- [ ] T027 [US3] Implement repeat/cache scenario comparison without invented cache claims in src/openrouter_demo/scenarios.py
- [ ] T028 [US3] Implement cache metadata and repeat-observation display fields in src/openrouter_demo/telemetry.py
- [ ] T029 [US3] Display repeat/cache comparison and eval summary in src/openrouter_demo/ui.py

**Checkpoint**: User Stories 1, 2, and 3 work independently through the UI or eval command.

---

## Phase 6: User Story 4 - Walk Through the Demo in an Interview (Priority: P4)

**Goal**: An interviewer can understand the project in 30 seconds, run the core walkthrough in five minutes after setup, and inspect the failure story.

**Independent Test**: Follow README.md and docs/failure-tree.md from a clean checkout with OPENROUTER_API_KEY and complete the quickstart scenarios.

### Tests for User Story 4

> Documentation validation is the quickstart smoke path for this story; no separate pytest file is required.

### Implementation for User Story 4

- [ ] T030 [US4] Write the five-minute project story and run instructions in README.md
- [ ] T031 [US4] Document client-to-OpenRouter-to-provider-to-telemetry diagnosis paths in docs/failure-tree.md
- [ ] T032 [US4] Document routing, fallback, latency, cost, cache/repeat, and eval architecture in docs/architecture.md
- [ ] T033 [US4] Add setup, demo, eval, and check command aliases to Makefile
- [ ] T034 [US4] Verify README.md does not present a separate FastAPI service or production SaaS architecture

**Checkpoint**: All user stories are independently demonstrable and ready for polish validation.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, hygiene, and constitution compliance across all user stories.

- [ ] T035 Update .env.example with every required and optional variable referenced by src/openrouter_demo/config.py and README.md
- [ ] T036 Review dependency list and remove unused packages from pyproject.toml
- [ ] T037 Validate no secret values are committed in .env.example, README.md, specs/001-openrouter-inference-lab/quickstart.md, and docs/failure-tree.md
- [ ] T038 Run uv sync and update uv.lock
- [ ] T039 Run uv run pytest and fix failures in tests/
- [ ] T040 Run uv run ruff check . and fix failures in src/openrouter_demo/, tests/, and app.py
- [ ] T041 Run uv run python app.py and validate User Story 1 and User Story 2 UI scenarios manually through app.py
- [ ] T042 Run uv run python -m openrouter_demo.evals and validate User Story 3 command output manually through src/openrouter_demo/evals.py
- [ ] T043 Validate README.md five-minute walkthrough against specs/001-openrouter-inference-lab/quickstart.md
- [ ] T044 Confirm all completed behavior satisfies specs/001-openrouter-inference-lab/contracts/local-demo-contract.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; MVP path.
- **User Story 2 (Phase 4)**: Depends on Foundational and benefits from US1 UI surfaces.
- **User Story 3 (Phase 5)**: Depends on Foundational and telemetry surfaces from US1.
- **User Story 4 (Phase 6)**: Can start after Foundational, but final documentation depends on US1-US3 behavior.
- **Polish (Phase 7)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1**: No user-story dependency after Foundational.
- **US2**: Requires routing strategies from Foundational and UI panels from US1 for visible demo evidence.
- **US3**: Requires telemetry normalization from Foundational and run evidence from US1.
- **US4**: Documents and validates US1-US3; can draft early, final pass last.

### Within Each User Story

- Tests for changed core logic before implementation.
- Models/config/routing/telemetry foundations before UI behavior.
- Scenario orchestration before UI display for that scenario.
- Story checkpoint validation before moving to the next priority when working sequentially.

### Parallel Opportunities

- T003, T004, and T005 can run in parallel after T001 begins.
- T007, T008, and T009 can run in parallel after T006 defines shared model names.
- T012, T018, T023, and T024 can be written in parallel because they touch separate test contracts or independent sections.
- T025 can run in parallel with T026 planning, but T026 cannot complete until T025 exists.
- T030, T031, and T032 can draft in parallel after the quickstart and contracts exist.
- T039 and T040 are separate commands but should run after implementation tasks are complete.

---

## Parallel Example: User Story 1

```text
Task: "T012 [US1] Add response streaming, unavailable metadata, and enabled/disabled Langfuse tracing tests in tests/test_response_handling.py"
Task: "T014 [US1] Implement telemetry capture plus optional Langfuse trace/generation creation and trace URL/status propagation in src/openrouter_demo/telemetry.py"
```

## Parallel Example: User Story 2

```text
Task: "T019 [US2] Implement provider routing request fields for cost and latency strategies in src/openrouter_demo/routing.py"
Task: "T020 [US2] Implement deterministic fallback trigger and fallback attempt recording in src/openrouter_demo/scenarios.py"
```

## Parallel Example: User Story 3

```text
Task: "T023 [US3] Add deterministic eval scoring tests in tests/test_eval_scoring.py"
Task: "T025 [US3] Create three to five deterministic eval cases in evals/cases.json"
```

## Parallel Example: User Story 4

```text
Task: "T030 [US4] Write the five-minute project story and run instructions in README.md"
Task: "T031 [US4] Document client-to-OpenRouter-to-provider-to-telemetry diagnosis paths in docs/failure-tree.md"
Task: "T032 [US4] Document routing, fallback, latency, cost, cache/repeat, and eval architecture in docs/architecture.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate streaming inference independently with `uv run python app.py`.
5. Demo if only the basic live streaming proof is needed.

### Incremental Delivery

1. Setup + Foundational -> shared models, config, client seams, routing, telemetry.
2. US1 -> live streaming response and honest metadata labels.
3. US2 -> routing/fallback reliability evidence.
4. US3 -> cost/latency/cache-or-repeat comparison and deterministic evals.
5. US4 -> README, architecture, failure tree, and walkthrough polish.
6. Polish -> uv, pytest, Ruff, secret hygiene, and quickstart validation.

### Parallel Team Strategy

With multiple implementers:

1. One implementer completes Setup and shared model/config contracts.
2. Split Foundation by files: routing.py, telemetry.py, client.py, scenarios.py.
3. After Foundation, implement US1 first enough to establish UI evidence panels.
4. US2, US3, and US4 documentation can then proceed with file-based coordination.

---

## Notes

- [P] tasks = different files, no dependency on incomplete tasks.
- [Story] label maps task to a specific user story for traceability.
- Each user story has an independent validation path.
- Tests for core logic are included because the constitution requires focused pytest coverage.
- Avoid adding a database, separate service, separate frontend, authentication, queues, Docker requirement, or broad UI polish.
