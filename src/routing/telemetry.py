"""Telemetry helpers for routing decisions and fallback events.

Provides a tiny in-memory latency store suitable for unit tests and local demo
instrumentation. Emits are no-ops that print events for now.
"""

from typing import Dict, Any, Optional

_latencies: Dict[str, list[float]] = {}


def record_latency(provider: str, latency_ms: float) -> None:
    _latencies.setdefault(provider, []).append(latency_ms)


def get_average_latency(provider: str) -> Optional[float]:
    data = _latencies.get(provider)
    if not data:
        return None
    return sum(data) / len(data)


def emit_routing_event(provider: str, strategy: str, metadata: Dict[str, Any]):
    # Placeholder: integrate with project's telemetry pipeline.
    print(f"ROUTING_EVENT provider={provider} strategy={strategy} metadata={metadata}")


def emit_fallback_event(attempted: list, final_provider: str):
    print(f"FALLBACK_EVENT attempted={attempted} final={final_provider}")
