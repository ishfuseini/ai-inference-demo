# Content Editing Guide

This guide is for contributors editing copy in the OpenRouter Production Inference Lab. Use it when changing UI labels, demo prompts, walkthrough language, docs, errors, empty states, or telemetry wording.

After reading this, you should be able to make a copy change that preserves the demo story: production inference is not just generated text; it is routing, observability, fallback, cost, latency, cache evidence, traces, and evals made inspectable.

## The Editing Principle

Every sentence should help a reviewer understand or operate the inference demo.

This project is a local interview lab, not a SaaS product and not a chatbot. Copy should make the operational evidence legible without overselling the system. Prefer precise, bounded language over broad product claims.

## Audience

Write for two readers:

- The interviewer, who needs to understand the demo quickly and ask useful technical questions.
- The candidate, who needs to narrate what is happening without hiding uncertainty.

Assume the reader understands Python, APIs, and LLM basics. Do not explain general concepts unless this project uses them in a specific way.

## Voice

Use a clear, technical, evidence-first voice.

Good copy sounds:

- direct
- inspectable
- calm under failure
- honest about missing metadata
- specific about what happened

Avoid copy that sounds:

- like a chatbot product
- like a benchmark leaderboard
- like a production SaaS pitch
- certain when the data is unavailable
- cute when a request failed

## Core Vocabulary

Use these terms consistently:

- **Inference run** for one prompt execution.
- **Strategy** for the selected routing approach.
- **Provider** for the upstream provider returned by the route when available.
- **Fallback** for recovery after a preferred route fails or is deliberately simulated to fail.
- **Telemetry** for runtime evidence such as latency, tokens, cost, provider, cache state, and trace state.
- **Trace** for the optional Langfuse observation link.
- **Eval** for deterministic checks used to compare behavior.

Avoid using **chat**, **assistant**, or **conversation** as the primary frame. The interface can accept prompts, but the product story is inference operations.

## Where to Edit

Use this map when you know the kind of content you need to change.

| To change | Edit |
| --- | --- |
| App title, UI labels, button text, sample prompts, empty states, telemetry labels, and tab names | `src/openrouter_demo/ui.py` |
| OpenRouter request errors, streaming error messages, and provider metadata handling | `src/openrouter_demo/client.py` |
| Strategy names, routing descriptions, and model/provider choices | `src/openrouter_demo/routing.py` |
| Langfuse trace wording and telemetry normalization behavior | `src/openrouter_demo/telemetry.py` |
| Repeat/cache scenario wording and fallback scenario behavior | `src/openrouter_demo/scenarios.py` |
| Deterministic eval case prompts and scoring criteria | `evals/cases.json` |
| The main project pitch, install flow, walkthrough links, and docs index | `README.md` |
| The five-minute spoken demo and interviewer Q&A | `docs/ux/demo-script.md` |
| The UI/UX screen behavior, hierarchy, and copy intent | `docs/ux/spec.md` |
| The visual design system, color tokens, spacing, and typography brief | `docs/design/DESIGN.md` |
| The clean-checkout validation path | `docs/specs/quickstart.md` |
| Failure diagnosis language and recovery paths | `docs/failure-tree.md` |
| Architecture explanation and component boundaries | `docs/architecture.md` |

When a copy change affects user-visible behavior, update the matching tests in `tests/` only when they assert that wording or structure intentionally. Do not loosen tests just to avoid updating expected copy.

## Evidence Rules

Copy must distinguish observed facts from unavailable data.

Use:

- "unavailable" when the provider or route did not return a field.
- "disabled" when an optional feature is intentionally off.
- "failed" when a request, trace, or scenario attempted work and did not complete.
- "simulated" when a failure path is intentionally triggered for a reproducible demo.

Do not write:

- "free" unless cost is actually known to be zero.
- "cached" unless cache evidence was returned.
- "best model" unless the eval evidence supports that exact claim.
- "production-ready platform" because the project is a local demo lab.

## UI Copy Rules

Labels should name the thing a user can inspect or do.

Good labels:

- "Run Inference"
- "Strategy"
- "Telemetry"
- "Run History"
- "Comparison"
- "Simulate failure"

Weak labels:

- "Submit"
- "Advanced"
- "Results"
- "Magic route"
- "Chat"

Buttons should use verbs when they perform an action. Section headings can use nouns when they name evidence areas.

## Prompt Copy

Sample prompts should feel like realistic production tasks. Keep them short enough to control cost and latency.

Good sample prompts:

- "Summarize this incident report for a customer."
- "Classify this support ticket by severity."

Avoid prompts that:

- invite long essays
- require private or proprietary context
- produce flashy but irrelevant output
- shift the demo toward general chat

## Error and Empty States

Error copy should name the problem and the recovery path.

Use this shape:

1. What happened.
2. Why it matters.
3. What to do next.

Example:

> OpenRouter credentials are missing. Live inference is disabled until the required API key is exported and the app is restarted.

Empty states should set expectations without sounding broken.

Example:

> Previous runs will appear here for route, fallback, cost, latency, cache, and trace review.

## Demo Script Rules

The spoken walkthrough should make one argument: operating inference requires evidence.

Keep the script anchored to this sequence:

1. Route intentionally.
2. Observe what happened.
3. Recover from failure.
4. Compare cost, latency, cache, and quality.
5. Change model behavior with evidence.

Do not add unsupported claims about scale, availability, security posture, or benchmark quality. The demo can show production reasoning without pretending to be a production service.

## Documentation Rules

Docs should help a fresh reader act correctly.

Before adding or changing a doc, name the reader and the action they should be able to take after reading. Remove background that does not help that action.

Prefer:

- short sections
- concrete expected outcomes
- bounded examples
- honest prerequisites
- commands only when the reader must run them

Avoid:

- session summaries
- implementation diary entries
- vague strategy language
- claims that duplicate what tests or telemetry should prove

## Editing Checklist

Before finishing a content change, check:

- Does the copy preserve the inference operations story?
- Does it avoid chatbot framing?
- Does it distinguish unavailable, disabled, failed, simulated, and observed values?
- Does it keep live-cost exposure small?
- Does it help the interviewer or candidate act within the five-minute demo?
- Does it avoid claims that the local lab cannot prove?
- If the wording appears in the UI, is it short enough to scan?

If the answer to any item is no, revise before shipping.
