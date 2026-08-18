# Phase 1: Runnable Skeleton and Config - Context

**Gathered:** 2026-08-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 creates the runnable local foundation for the OpenRouter Production Inference Lab: dependency setup, exported-env configuration, a thin NiceGUI app shell, visible credential readiness, seed setup docs, and an importable Python package layout. It must prove the reviewer can run `uv sync` and `uv run python app.py` without secrets in git. It must not implement live OpenRouter inference, routing/fallback behavior, eval execution, cache/repeat claims, or Langfuse trace creation yet.

</domain>

<decisions>
## Implementation Decisions

### Scaffold Shape
- **D-01:** Create the full importable scaffold in Phase 1: `app.py`, `pyproject.toml`, `uv.lock`, `.env.example`, package modules for UI/client/routing/scenarios/telemetry/evals/models/config, `tests/`, and `evals/`. Later phases fill behavior without reshaping the repo.
- **D-02:** Stub modules may exist, but they must be honest and importable. They must not pretend later telemetry, routing, fallback, cache, eval, or live inference behavior exists.

### Configuration And Credentials
- **D-03:** Make `.env.example` immediately useful as the credential checklist, with required `OPENROUTER_API_KEY` and optional Langfuse variables.
- **D-04:** Runtime configuration reads exported environment variables only through `os.environ`; do not add dotenv parsing or a dotenv dependency in Phase 1.
- **D-05:** Missing `OPENROUTER_API_KEY` launches a real NiceGUI setup/status shell and does not attempt any live request.
- **D-06:** Missing Langfuse credentials are visibly shown as optional/disabled and do not block launch.
- **D-07:** `.env.example` must contain variable names and comments only, never secret-like values.

### App Shell
- **D-08:** The first NiceGUI screen should structurally resemble the intended inference operations console, with setup state and disabled/empty panels rather than fake inference behavior.
- **D-09:** Visual polish is not a Phase 1 priority because the user plans to run `impeccable` afterward for UI touches. Keep the shell clean and understandable, but avoid spending Phase 1 on high-fidelity styling.

### Documentation
- **D-10:** Add minimal README setup documentation now: install, env vars, launch, and clearly marked future demo capabilities. The full interview walkthrough remains Phase 6.

### Dependencies And Verification
- **D-11:** Include the whole planned dependency stack now: NiceGUI, httpx, Langfuse SDK, pytest, Ruff, and Python 3.12+ via `uv`.
- **D-12:** Phase 1 verification should prove setup and imports only: `uv sync`, config/import/env behavior tests, Ruff, and launch smoke check without any live OpenRouter request.

### the agent's Discretion
- The implementer may choose simple names and minimal stub contents that match Python project conventions, as long as the scaffold boundaries above remain clear.
- The implementer may keep README wording concise and setup-focused; final demo storytelling belongs in Phase 6.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Planning Scope
- `.planning/PROJECT.md` - Defines project purpose, constraints, out-of-scope boundaries, and key stack decisions.
- `.planning/REQUIREMENTS.md` - Defines Phase 1 requirements SETUP-01 through SETUP-06 and broader v1 traceability.
- `.planning/ROADMAP.md` - Defines Phase 1 goal, dependencies, success criteria, and phase boundary.
- `.planning/STATE.md` - Confirms current focus is Phase 1 and records accumulated project decisions.

### Seed Product Specs
- `docs/PRD.md` - Defines the local inference lab story, target repo layout, and NiceGUI/OpenRouter/Langfuse architecture.
- `docs/specs/acceptance-criteria.md` - Lists demo-critical, UI/UX, eval, and repository acceptance criteria.
- `docs/specs/quickstart.md` - Defines canonical setup and run commands plus troubleshooting expectations.
- `docs/specs/contracts/local-demo-contract.md` - Defines local UI/command contracts and negative requirements.
- `docs/specs/data-model.md` - Defines future typed entities; Phase 1 should scaffold toward these without implementing behavior prematurely.
- `docs/specs/research.md` - Locks direct OpenRouter HTTPS, NiceGUI local UI, optional Langfuse, env vars, deterministic evals, and uv/Ruff/pytest decisions.

### UI And Interview Intent
- `docs/ux/screen-spec.md` - Defines the intended one-screen operations-console structure, states, labels, and metadata language.
- `docs/design/DESIGN-light.md` - Provides visual direction for later UI polish; Phase 1 should only apply enough structure to avoid fighting it later.

### Research Context
- `.planning/research/ARCHITECTURE.md` - Defines internal package boundaries and data flow for later phases.
- `.planning/research/PITFALLS.md` - Highlights setup, metadata honesty, streaming, fallback, and Langfuse pitfalls.
- `.planning/research/SUMMARY.md` - Summarizes stack, architecture confidence, phase ordering, and known research gaps.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Seed docs in `docs/` and planning docs in `.planning/` are the primary reusable assets. There is no implemented app/source scaffold yet.
- `data/api-complaint.csv` and `data/api-complaint-rubric.md` can remain seed eval/demo material for later phases, but Phase 1 should not wire eval execution.

### Established Patterns
- The repo currently establishes product and architecture decisions through docs, not code.
- The intended code pattern is a single Python package with a thin `app.py` entrypoint and separate modules for config, UI, client, routing, scenarios, telemetry, evals, and typed models.
- Runtime state should stay local/in-memory in later phases; Phase 1 does not need persistence.

### Integration Points
- `app.py` will be the reviewer launch path for `uv run python app.py`.
- `src/openrouter_demo/config.py` should own environment inspection and expose setup state to the UI.
- `src/openrouter_demo/ui.py` should render the setup/status shell and future operations-console structure.
- Tests should focus on config behavior and importability in this phase.

</code_context>

<specifics>
## Specific Ideas

- User explicitly wants `.env.example` sketched early so they can prepare credentials quickly.
- User plans to run `impeccable` after Phase 1 for UI touches, so Phase 1 should avoid over-investing in visual polish.

</specifics>

<deferred>
## Deferred Ideas

- Live OpenRouter streaming request - Phase 2.
- Routing and reproducible fallback behavior - Phase 3.
- Honest normalized telemetry, repeat/cache observations, and optional Langfuse traces - Phase 4.
- Deterministic eval command and comparison output - Phase 5.
- Full interview README/walkthrough and final quality-gate polish - Phase 6.

</deferred>

---

*Phase: 1-Runnable Skeleton and Config*
*Context gathered: 2026-08-18*
