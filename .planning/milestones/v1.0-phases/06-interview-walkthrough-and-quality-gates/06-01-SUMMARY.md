---
phase: 06-interview-walkthrough-and-quality-gates
plan: 01
subsystem: docs
tags: [docs, architecture, failure-tree, readme, drift-guard, pytest]

requires:
  - phase: 05-deterministic-evals
    provides: "evals.py CLI, canonical eval command PYTHONPATH=src uv run python -m openrouter_demo.evals, ui.py literal copy constants"
provides:
  - "README.md rewritten to the full demo story (route/observe/recover/evaluate) with setup, env vars, walkthrough, eval command, and quality gates"
  - "docs/architecture.md promoting the Component Boundaries table, mermaid data-flow diagram, patterns, and anti-patterns"
  - "docs/failure-tree.md at the quickstart-expected path with all eight categories and UI copy reconciled to literal ui.py constants"
  - "tests/test_docs.py drift guard pinning the three docs and the canonical eval command"
affects: [Phase 6 plans 06-02 (DOC-04/DOC-05 guards), 06-03 (quality-gate confirmation)]

actuals:
  tokens: 6000
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Path(...).read_text() + plain-assert doc-vs-code drift guards (mirrors tests/test_config.py)"
    - "Promote-not-invent: docs/architecture.md mirrors .planning/research/ARCHITECTURE.md section names verbatim"

key-files:
  created:
    - docs/architecture.md
    - docs/failure-tree.md
    - tests/test_docs.py
  modified:
    - README.md
    - docs/specs/quickstart.md
  deleted:
    - docs/specs/failure-tree.md

key-decisions:
  - "Failure tree moved (git mv) to docs/failure-tree.md so exactly one canonical path exists; quickstart already expected that path"
  - "README states the app reads exported env vars only and never parses .env (no python-dotenv; config.py reads os.environ)"
  - "Failure-tree User-facing copy snippets reconciled to literal ui.py constants; the cache-repeat example is annotated illustrative (no literal match)"
  - "docs/architecture.md treats FastAPI only as NiceGUI's internal implementation detail, never a product layer"

patterns-established:
  - "Guard tests read docs with Path(...).read_text() and assert exact substrings (canonical eval command, headings, category terms)"

requirements-completed: [DOC-01, DOC-02, DOC-03]

coverage:
  - id: D1
    description: "README.md rewritten to the demo story, setup, env vars, and five-minute walkthrough with six pinned substrings and canonical eval command"
    requirement: DOC-01
    verification:
      - kind: unit
        ref: "tests/test_config.py#test_readme_documents_setup"
        status: pass
      - kind: unit
        ref: "tests/test_docs.py#test_readme_documents_eval_command"
        status: pass
    human_judgment: false
  - id: D2
    description: "docs/architecture.md with Component Boundaries table, mermaid data-flow diagram, patterns, and anti-patterns"
    requirement: DOC-02
    verification:
      - kind: unit
        ref: "tests/test_docs.py#test_architecture_guide_exists"
        status: pass
    human_judgment: false
  - id: D3
    description: "docs/failure-tree.md at canonical path with all eight categories and quickstart step 6 using the canonical eval command"
    requirement: DOC-03
    verification:
      - kind: unit
        ref: "tests/test_docs.py#test_failure_tree_and_quickstart_paths_resolve"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-08-20
status: complete
---

# Phase 06 Plan 01 Summary: Docs slice (DOC-01/02/03)

The repo's three reviewer-facing documents are now truthful and pinned against drift: a rewritten README, a promoted architecture guide, and a relocated failure tree whose UI copy matches the literal `ui.py` constants.

## Performance

- **Duration:** ~8 min
- **Started:** 2026-08-20T16:45:00Z
- **Completed:** 2026-08-20T16:53:47Z
- **Tasks:** 3 completed
- **Files modified:** 5 (plus 1 deleted)

## Accomplishments

- `README.md` rewritten from a stale Phase-1 status page to the full story (route/observe/recover/evaluate), with the six pinned substrings preserved and the canonical eval command documented.
- `docs/architecture.md` created by promoting `.planning/research/ARCHITECTURE.md` — Component Boundaries table, mermaid `flowchart LR` data flow, patterns, and anti-patterns.
- `docs/failure-tree.md` moved to the quickstart-expected path with all eight DOC-03 categories intact and User-facing copy reconciled to literal `ui.py` constants.
- `docs/specs/quickstart.md` step 6 fixed to `PYTHONPATH=src uv run python -m openrouter_demo.evals`.
- `tests/test_docs.py` drift guard pins all three docs and the canonical eval command; 3 tests pass.

## Task Commits

Each task was committed atomically:

1. **Task 1: create docs/architecture.md and pin it** - `6d690b4` (docs)
2. **Task 2: rewrite README.md for DOC-01** - `749f3c1` (docs)
3. **Task 3: move failure tree and fix quickstart** - `d456662` (docs)

## Files Created/Modified

- `docs/architecture.md` — promoted architecture guide with Component Boundaries and mermaid data flow
- `docs/failure-tree.md` — relocated failure tree with reconciled UI copy
- `docs/specs/failure-tree.md` — deleted (source of the move)
- `docs/specs/quickstart.md` — eval command + file links fixed
- `README.md` — rewritten story, setup, env vars, walkthrough
- `tests/test_docs.py` — created with three drift-guard tests

## Decisions Made

- Moved the failure tree with `git mv` so git history is preserved and exactly one canonical path exists.
- Kept `docs/architecture.md` structure identical to the research artifact's section names (promote-not-invent).
- Annotated the cache-repeat example as illustrative rather than fabricating a literal UI string.

## Deviations from Plan

None - plan executed exactly as written.
