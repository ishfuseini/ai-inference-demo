---
phase: 06-interview-walkthrough-and-quality-gates
plan: 02
subsystem: testing
tags: [pytest, guard-tests, ui-framing, coverage]

requires:
  - phase: 06-interview-walkthrough-and-quality-gates
    provides: "tests/test_docs.py drift guard (extended here), literal ui.py copy constants"
provides:
  - "DOC-04 guard: tests/test_ui.py::test_ui_has_no_chatbot_labels pins inference-operation copy and rejects conversation-assistant vocabulary"
  - "DOC-05 guard: tests/test_docs.py::test_focused_test_coverage pins the four focus areas to existing passing test files"
affects: [Phase 6 plan 06-03 (quality-gate confirmation)]

actuals:
  tokens: 2000
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Path(...).read_text() source-inspection guards (mirrors tests/test_phase1_guards.py)"
    - "Assert named test functions exist by substring rather than asserting exact counts"

key-files:
  created: []
  modified:
    - tests/test_ui.py
    - tests/test_docs.py

key-decisions:
  - "DOC-04 forbidden list: ui.chat_message, double-quoted role strings \"assistant\"/\"user\", and UI-label terms Chat / Send message"
  - "DOC-05 pins file existence + named test functions, not exact test counts (counts grow over time)"
  - "No src/ code changes: DOC-04/DOC-05 were already satisfied by Phases 1-5"

patterns-established:
  - "Guard tests pin already-correct source against future drift without modifying it"

requirements-completed: [DOC-04, DOC-05]

coverage:
  - id: D1
    description: "DOC-04 UI-framing guard rejecting chatbot vocabulary and pinning inference-operation copy"
    requirement: DOC-04
    verification:
      - kind: unit
        ref: "tests/test_ui.py#test_ui_has_no_chatbot_labels"
        status: pass
    human_judgment: false
  - id: D2
    description: "DOC-05 focused-test coverage guard pinning the four focus areas to existing test files"
    requirement: DOC-05
    verification:
      - kind: unit
        ref: "tests/test_docs.py#test_focused_test_coverage"
        status: pass
    human_judgment: false

duration: 3min
completed: 2026-08-20
status: complete
---

# Phase 06 Plan 02 Summary: Guard-tests slice (DOC-04/05)

DOC-04 and DOC-05 are now enforced by tests rather than merely verified by research: the UI framing and the four focused test-coverage areas are pinned against future drift, with no `src/` changes.

## Performance

- **Duration:** ~3 min
- **Started:** 2026-08-20T16:55:00Z
- **Completed:** 2026-08-20T17:00:00Z
- **Tasks:** 2 completed
- **Files modified:** 2

## Accomplishments

- `tests/test_ui.py` gained `test_ui_has_no_chatbot_labels`, asserting the inference-operation copy is present and the forbidden conversation-assistant vocabulary is absent from `ui.py` source.
- `tests/test_docs.py` gained `test_focused_test_coverage`, pinning response/error, routing, telemetry, and eval scoring to existing passing test files and named test functions.
- `src/openrouter_demo/ui.py` is unchanged (verified with `git diff --exit-code`).

## Task Commits

1. **Task 1: add DOC-04 UI-framing guard** - `bdd6a52` (test)
2. **Task 2: add DOC-05 focused-test coverage guard** - `146463d` (test)

## Files Created/Modified

- `tests/test_ui.py` — added `test_ui_has_no_chatbot_labels`
- `tests/test_docs.py` — added `test_focused_test_coverage`

## Decisions Made

- Forbidden-vocabulary list chosen so every term is verifiably absent from `ui.py` (verified zero false positives on first run).
- DOC-05 guard asserts named test functions rather than exact counts, so the guard does not break as the suite grows.

## Deviations from Plan

None - plan executed exactly as written.
