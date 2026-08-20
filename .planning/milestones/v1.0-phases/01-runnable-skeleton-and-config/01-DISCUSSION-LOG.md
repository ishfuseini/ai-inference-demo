# Phase 1: Runnable Skeleton and Config - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-08-18
**Phase:** 1-Runnable Skeleton and Config
**Areas discussed:** Skeleton shape, environment loading, missing credential behavior, UI shell, setup docs, dependencies, verification

---

## Gray Area Selection

| Option | Description | Selected |
|--------|-------------|----------|
| All core areas | Covers skeleton depth, credential/setup behavior, and first-screen shell fidelity before context is written. | yes |
| Setup behavior | Focuses on env loading, missing API-key guidance, optional Langfuse state, and canonical run commands. | |
| Skeleton shape | Focuses on how much package/module/test/UI structure Phase 1 should create without implementing later inference. | |

**User's choice:** All core areas.
**Notes:** Discuss the decisions that affect Phase 1 planning.

---

## Skeleton Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Full importable scaffold | Create `.env.example` plus `app.py`, `pyproject.toml`, package modules, tests/evals dirs, and minimal importable stubs for later phases. | yes |
| Config-first slice | Create `pyproject.toml`, `app.py`, config module, `.env.example`, and a minimal UI; defer other modules until later phases. | |
| Just setup files | Create `pyproject.toml`, `.env.example`, README/setup notes, and the thinnest app launch path possible. | |

**User's choice:** Full importable scaffold.
**Notes:** User first said, "if you sketch out env.example i can get that ready asap", so `.env.example` should be ready immediately.

---

## Environment Loading

| Option | Description | Selected |
|--------|-------------|----------|
| Shell env only | Use `os.environ` and `.env.example`; no dotenv dependency added in Phase 1. | yes |
| Auto-load `.env` | Support a local `.env` file automatically for convenience, adding the minimal dependency or parser needed. | |
| Document both only | Runtime reads shell env; docs mention export commands and local `.env` patterns without app-level loading. | |

**User's choice:** Shell env only.
**Notes:** `.env.example` is documentation/checklist, not a file the app parses.

---

## Missing Credential Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Setup status shell | Launch a real NiceGUI shell with visible OpenRouter missing and Langfuse optional/disabled states, with no live call attempt. | yes |
| Instruction page only | Show only setup instructions until the required key is present. | |
| Main shell plus error | Show the normal app shell and place setup guidance near the future run controls. | |

**User's choice:** Setup status shell.
**Notes:** The app must launch even when `OPENROUTER_API_KEY` is absent.

---

## UI Shell

| Option | Description | Selected |
|--------|-------------|----------|
| Operations skeleton | Use the intended header/request/response/telemetry layout, but keep controls disabled or empty until later phases. | yes |
| Setup-only screen | Show only config readiness and launch instructions; introduce the operations console in Phase 2. | |
| Hybrid setup first | Show setup readiness at top with a small preview of the future operations sections below. | |

**User's choice:** Operations skeleton.
**Notes:** User said, "ill run impeccable after for ui touches", so Phase 1 should not over-focus on visual polish.

---

## Setup Documentation

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal README setup | Create/update README with install, env vars, launch, and clearly marked future demo capabilities; full walkthrough stays Phase 6. | yes |
| Env example only | Only add `.env.example` and rely on existing docs/specs until the final documentation phase. | |
| Full README now | Write the complete interview README and walkthrough now, updating later if behavior changes. | |

**User's choice:** Minimal README setup.
**Notes:** Final interview walkthrough is deferred to Phase 6.

---

## Dependencies

| Option | Description | Selected |
|--------|-------------|----------|
| Whole planned stack | Install NiceGUI, httpx, Langfuse SDK, pytest, and Ruff now so `uv sync` proves the intended environment early. | yes |
| Only Phase 1 deps | Install NiceGUI plus pytest/Ruff now; add httpx/Langfuse when inference and tracing are implemented. | |
| Runtime minimal | Install only what `app.py` needs to launch, deferring dev/test and inference dependencies. | |

**User's choice:** Whole planned stack.
**Notes:** Phase 1 should commit the lockfile even if later modules start as stubs.

---

## Verification

| Option | Description | Selected |
|--------|-------------|----------|
| Setup and imports | Run `uv sync`, pytest config/import/env behavior tests, Ruff, and launch smoke check without any live OpenRouter request. | yes |
| Manual launch only | Keep automated tests minimal or absent in Phase 1; rely mainly on `uv sync` and app launch. | |
| Broader stub tests | Add tests for placeholder routing/telemetry/eval models now, even before those behaviors are implemented. | |

**User's choice:** Setup and imports.
**Notes:** Phase 1 verification should not call OpenRouter.

---

## Final Check

| Option | Description | Selected |
|--------|-------------|----------|
| Ready for context | Use these decisions to prepare the Phase 1 context/documentation plan. | yes |
| Discuss env example | Go deeper on exact `.env.example` variable names and comments before locking context. | |
| Discuss app shell | Go deeper on the skeleton screen's labels, disabled states, and visible setup guidance. | |

**User's choice:** Ready for context.
**Notes:** No further Phase 1 gray areas requested.

## the agent's Discretion

- The implementer may choose simple scaffold names and minimal stub content that preserve the approved boundaries.
- The implementer may keep setup documentation concise.

## Deferred Ideas

- Live OpenRouter streaming request - Phase 2.
- Routing and reproducible fallback behavior - Phase 3.
- Honest normalized telemetry, repeat/cache observations, and optional Langfuse traces - Phase 4.
- Deterministic eval command and comparison output - Phase 5.
- Full interview walkthrough and final docs/quality polish - Phase 6.
