# Phase 5 — API Coverage Declaration

**Phase:** 05-deterministic-evals
**Scope:** deterministic eval CLI (`src/openrouter_demo/evals.py`) + `evals/cases.json`
**Result:** No external API integration — no coverage matrix required.

## Declaration

Phase 5 introduces **no new external API or SDK integration**. It reuses two already-decided,
already-implemented surfaces:

1. **OpenRouter Chat Completions** — `src/openrouter_demo/client.py::stream_chat_completion`
   (`https://openrouter.ai/api/v1/chat/completions`, `Authorization: Bearer`, `X-OpenRouter-Metadata`,
   SSE parsing, usage/cost extraction, provider/routing metadata). This surface was decided in
   Phase 2 (Streaming Inference Evidence) and extended in Phases 3-4. Phase 5 composes it unchanged:
   `run_eval_case` consumes the stream exactly as `ui._run_inference` does, and `--models` routes
   through the already-first-class `stream_chat_completion(model=...)` override.

2. **Langfuse tracing** — `src/openrouter_demo/telemetry.py::record_trace` (`get_client`,
   `start_as_current_observation`, `flush`, `get_trace_url`). This surface was decided and
   implemented in Phase 4. Phase 5 calls `record_trace` with a distinct trace name
   (`eval-<case_id>`) and never constructs a Langfuse client directly — the Phase 1 guard
   (`test_phase1_keeps_langfuse_tracing_isolated_to_telemetry`) now also covers `evals.py`.

Because the api-coverage detector would fire only on the "OpenRouter"/"Langfuse" tokens that
already belong to previously-audited phases, no new endpoint, credential, request/response
contract, or SDK surface needs enumerating for Phase 5. The existing Phase 2 OpenRouter coverage
and Phase 4 Langfuse coverage remain authoritative.

**Note:** the api-coverage detector is not available in this planning session; this declaration
is provided in its place per the phase's api-coverage checkpoint.
