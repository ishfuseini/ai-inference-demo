"""Routing layer for selecting provider/model and handling fallbacks.

This implements basic telemetry emits via the project's telemetry helpers as a starting
point for Phase 3 implementation.
"""

from typing import List, Dict, Any, Optional

from routing.telemetry import emit_routing_event, emit_fallback_event, get_average_latency


class RoutingStrategy:
    PRIORITY = "priority"
    ROUND_ROBIN = "round_robin"
    LATENCY = "latency"


class Router:
    def __init__(self, providers: List[str]):
        if not providers:
            raise ValueError("Router requires a non-empty list of providers")
        self.providers = providers
        self._rr_index = 0

    def select_provider(self, strategy: str) -> str:
        """Select a provider based on the requested strategy.

        Returns the provider key/name.
        """
        if strategy == RoutingStrategy.PRIORITY:
            return self.providers[0]
        if strategy == RoutingStrategy.ROUND_ROBIN:
            provider = self.providers[self._rr_index % len(self.providers)]
            self._rr_index += 1
            return provider
        if strategy == RoutingStrategy.LATENCY:
            # Consult telemetry average latencies; pick the provider with the lowest average
            latencies = {p: get_average_latency(p) for p in self.providers}
            # filter out providers without latency data (None), prefer known latencies
            known = {p: l for p, l in latencies.items() if l is not None}
            if known:
                # pick provider with lowest average latency
                return min(known, key=lambda p: known[p])
            # fallback to priority if no telemetry available
            return self.providers[0]
        # Fallback default
        return self.providers[0]

    def call_with_fallback(self, strategy: str, call_fn, fallback_order: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """Attempt call using selected provider, then fall back to others on failure.

        call_fn(provider, **kwargs) should raise an exception on failure.
        Returns dict with keys: provider, result, attempted
        """
        attempted = []
        primary = self.select_provider(strategy)
        order = [primary]
        if fallback_order:
            # include fallback order but avoid duplicates
            order += [p for p in fallback_order if p not in order]
        # finally append remaining providers
        order += [p for p in self.providers if p not in order]

        last_exc = None
        for provider in order:
            attempted.append(provider)
            try:
                result = call_fn(provider, **kwargs)
                # emit routing event (non-blocking)
                try:
                    emit_routing_event(provider=provider, strategy=strategy, metadata={"attempted": attempted})
                except Exception:
                    # telemetry must not break the call path
                    pass
                return {"provider": provider, "result": result, "attempted": attempted}
            except Exception as e:
                last_exc = e
                # continue to next provider
                continue
        # if all fail, emit fallback event (non-blocking) and raise last exception
        try:
            emit_fallback_event(attempted=attempted, final_provider=attempted[-1] if attempted else "")
        except Exception:
            pass
        raise last_exc
