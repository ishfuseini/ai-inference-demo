# API Coverage Matrix — Phase 3: Routing and Fallback Demo

**Created:** 2026-08-19
**API:** OpenRouter Chat Completions (`/api/v1/chat/completions`)

## Coverage Matrix

| Capability | Status | Phase | Decision | Reason |
|------------|--------|-------|----------|--------|
| Chat completions (streaming) | INTEGRATED | 2 | INTEGRATE | Already implemented in Phase 2 via `stream_chat_completion` in `client.py`. No changes needed. |
| Provider routing: `sort` by price | NEW | 3 | INTEGRATE | Cost strategy sends `provider: {"sort": "price"}` in request body. Core to ROUTE-01. |
| Provider routing: `sort` by latency | NEW | 3 | INTEGRATE | Latency strategy sends `provider: {"sort": "latency"}` in request body. Core to ROUTE-01. |
| Provider routing: `allow_fallbacks` | NEW | 3 | INTEGRATE | Fallback primary strategy sends `provider: {"allow_fallbacks": false}` for deterministic 404 failure. Core to ROUTE-04. |
| Provider routing: `order` | — | — | OPT-OUT | Not needed for demo. `sort` covers the three strategy tradeoffs. Defer to potential Phase 4+ enhancement. |
| Provider routing: `only` / `ignore` | — | — | OPT-OUT | Over-constrains the demo. Pitfall 2 (Moderate): "Over-Constrained Routing" warns this can prevent fallback or make routes unavailable. |
| Provider routing: `preferred_max_latency` | — | — | OPT-OUT | `sort: "latency"` is simpler and sufficient for the demo. Could be a Phase 4 enhancement per research. |
| Provider routing: `preferred_min_throughput` | — | — | OPT-OUT | Not relevant to the demo's three-strategy comparison scope. |
| Provider routing: `max_price` | — | — | OPT-OUT | `sort: "price"` covers cost optimization. `max_price` adds a hard cutoff that could eliminate all providers in a demo setting. |
| Provider routing: `require_parameters` | — | — | OPT-OUT | Not relevant. No tool-use or structured-output features in the demo. |
| Provider routing: `data_collection` | — | — | OPT-OUT | Not relevant to routing strategy comparison. Applies to privacy policy enforcement, not cost/latency tradeoffs. |
| Provider routing: `quantizations` | — | — | OPT-OUT | Not relevant. Demo uses a single model slug; quantization filtering adds unnecessary complexity. |
| Provider routing: `zdr` | — | — | OPT-OUT | Not relevant to the demo scope. Zero-data-retention is a compliance filter, not a routing strategy. |
| Model fallbacks (`models` array) | — | — | OPT-OUT | Server-side model fallback hides primary failure from the client — fails ROUTE-05 and ROUTE-06. Client-side two-attempt orchestration used instead. [VERIFIED: openrouter.ai/docs/guides/routing/model-fallbacks] |
| Router metadata (`X-OpenRouter-Metadata` header) | INTEGRATED | 2 | INTEGRATE | Already handled in Phase 2 via `_extract_provider` and `_extract_model` in `client.py`. No changes needed in Phase 3. |

## Summary

- **INTEGRATED**: 5 capabilities (3 from Phase 2, 2 new in Phase 3)
- **NEW in Phase 3**: 3 capabilities (`sort: price`, `sort: latency`, `allow_fallbacks: false`)
- **OPT-OUT**: 11 capabilities (deferred or not applicable to demo scope)

## Verification

Each INTEGRATED capability is verified by automated tests:

| Capability | Test File | Test Assertion |
|------------|-----------|----------------|
| `sort: price` | `tests/test_routing.py` | `strategy_payload(COST_STRATEGY)["provider"] == {"sort": "price"}` |
| `sort: latency` | `tests/test_routing.py` | `strategy_payload(LATENCY_STRATEGY)["provider"] == {"sort": "latency"}` |
| `allow_fallbacks: false` | `tests/test_routing.py` | `strategy_payload(FALLBACK_PRIMARY_STRATEGY)["provider"] == {"allow_fallbacks": False}` |
| Streaming (existing) | `tests/test_client.py` | Existing Phase 2 tests |
| Router metadata (existing) | `tests/test_client.py` | Existing Phase 2 tests |