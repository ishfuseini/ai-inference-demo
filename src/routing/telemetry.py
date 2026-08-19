"""Telemetry helpers for routing decisions and fallback events.

Minimal helpers to be expanded during implementation.
"""

from typing import Dict, Any


def emit_routing_event(provider: str, strategy: str, metadata: Dict[str, Any]):
    # Placeholder: integrate with project's telemetry pipeline.
    print(f"ROUTING_EVENT provider={provider} strategy={strategy} metadata={metadata}")


def emit_fallback_event(attempted: list, final_provider: str):
    print(f"FALLBACK_EVENT attempted={attempted} final={final_provider}")
