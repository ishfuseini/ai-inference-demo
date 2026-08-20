from dataclasses import dataclass
from typing import Any


@dataclass
class FallbackAttempt:
    provider: str
    reason: str | None
    latency_ms: float | None


@dataclass
class RunRecord:
    id: str
    timestamp: str
    strategy: str
    provider: str
    model: str | None
    latency_ms: float | None
    tokens: int | None
    cost: float | None
    fallback_attempts: list[FallbackAttempt]
    trace_id: str | None
    raw_response: dict[str, Any] | None
