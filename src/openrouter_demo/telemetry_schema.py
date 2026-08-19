from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class FallbackAttempt:
    provider: str
    reason: Optional[str]
    latency_ms: Optional[float]


@dataclass
class RunRecord:
    id: str
    timestamp: str
    strategy: str
    provider: str
    model: Optional[str]
    latency_ms: Optional[float]
    tokens: Optional[int]
    cost: Optional[float]
    fallback_attempts: List[FallbackAttempt]
    trace_id: Optional[str]
    raw_response: Optional[Dict[str, Any]]
