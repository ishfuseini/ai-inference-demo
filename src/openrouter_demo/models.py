from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


@dataclass(frozen=True)
class Unavailable:
    label: str = "unavailable"

    def __bool__(self) -> bool:
        return False


UNAVAILABLE = Unavailable()


class Status(StrEnum):
    PENDING = "pending"
    STREAMING = "streaming"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class StreamChunk:
    text_delta: str


@dataclass(frozen=True)
class StreamedResult:
    text: str
    model: str | Unavailable
    provider: str | Unavailable
    prompt_tokens: int | Unavailable
    completion_tokens: int | Unavailable
    total_tokens: int | Unavailable
    cost_usd: float | Unavailable
    latency_ms: int


@dataclass(frozen=True)
class TelemetryEvidence:
    model: str | Unavailable
    provider: str | Unavailable
    latency_ms: int
    prompt_tokens: int | Unavailable
    completion_tokens: int | Unavailable
    total_tokens: int | Unavailable
    cost_usd: float | Unavailable


@dataclass(frozen=True)
class InferenceRun:
    run_id: str
    prompt: str
    strategy_name: str
    started_at: datetime
    completed_at: datetime | None
    status: Status
    streamed_text: str
    error_message: str | None
    telemetry: TelemetryEvidence | None