from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


@dataclass(frozen=True)
class Unavailable:
    label: str = "unavailable"


UNAVAILABLE = Unavailable()

_UNAVAILABLE_SENTINEL = "__unavailable__"


def serialize_value(value: object) -> object:
    if isinstance(value, Unavailable):
        return _UNAVAILABLE_SENTINEL
    return value


def deserialize_value(value: object) -> object:
    if value == _UNAVAILABLE_SENTINEL:
        return UNAVAILABLE
    return value


class Status(StrEnum):
    SUCCEEDED = "succeeded"
    FALLBACK_SUCCEEDED = "fallback_succeeded"
    FAILED = "failed"


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
    cache_status: str | Unavailable = UNAVAILABLE
    cached_tokens: int | Unavailable = UNAVAILABLE
    cache_write_tokens: int | Unavailable = UNAVAILABLE
    openrouter_metadata: dict | Unavailable = UNAVAILABLE


@dataclass(frozen=True)
class TelemetryEvidence:
    model: str | Unavailable
    provider: str | Unavailable
    latency_ms: int
    prompt_tokens: int | Unavailable
    completion_tokens: int | Unavailable
    total_tokens: int | Unavailable
    cost_usd: float | Unavailable
    cache_status: str | Unavailable = UNAVAILABLE
    cached_tokens: int | Unavailable = UNAVAILABLE
    cache_write_tokens: int | Unavailable = UNAVAILABLE
    trace_status: str | Unavailable = UNAVAILABLE
    trace_id: str | None = None
    trace_url: str | None = None
    observation_id: str | None = None
    openrouter_metadata: dict | Unavailable = UNAVAILABLE

    def to_dict(self) -> dict:
        return {
            "model": serialize_value(self.model),
            "provider": serialize_value(self.provider),
            "latency_ms": self.latency_ms,
            "prompt_tokens": serialize_value(self.prompt_tokens),
            "completion_tokens": serialize_value(self.completion_tokens),
            "total_tokens": serialize_value(self.total_tokens),
            "cost_usd": serialize_value(self.cost_usd),
            "cache_status": serialize_value(self.cache_status),
            "cached_tokens": serialize_value(self.cached_tokens),
            "cache_write_tokens": serialize_value(self.cache_write_tokens),
            "trace_status": serialize_value(self.trace_status),
            "trace_id": self.trace_id,
            "trace_url": self.trace_url,
            "observation_id": self.observation_id,
            "openrouter_metadata": serialize_value(self.openrouter_metadata),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TelemetryEvidence":
        return cls(
            model=deserialize_value(data.get("model")),
            provider=deserialize_value(data.get("provider")),
            latency_ms=data.get("latency_ms"),
            prompt_tokens=deserialize_value(data.get("prompt_tokens")),
            completion_tokens=deserialize_value(data.get("completion_tokens")),
            total_tokens=deserialize_value(data.get("total_tokens")),
            cost_usd=deserialize_value(data.get("cost_usd")),
            cache_status=deserialize_value(data.get("cache_status")),
            cached_tokens=deserialize_value(data.get("cached_tokens")),
            cache_write_tokens=deserialize_value(data.get("cache_write_tokens")),
            trace_status=deserialize_value(data.get("trace_status")),
            trace_id=data.get("trace_id"),
            trace_url=data.get("trace_url"),
            observation_id=data.get("observation_id"),
            openrouter_metadata=deserialize_value(data.get("openrouter_metadata")),
        )


@dataclass(frozen=True)
class LangfuseScore:
    id: str
    name: str
    value: float | bool | str
    data_type: str  # NUMERIC | BOOLEAN | CATEGORICAL | TEXT | CORRECTION
    source: str
    timestamp: str
    trace_id: str | None = None
    observation_id: str | None = None
    comment: str | None = None

    @property
    def display_value(self) -> str:
        if self.data_type == "BOOLEAN":
            return "True" if bool(self.value) else "False"
        return str(self.value)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "value": serialize_value(self.value),
            "data_type": self.data_type,
            "source": self.source,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "observation_id": self.observation_id,
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LangfuseScore":
        return cls(
            id=data["id"],
            name=data["name"],
            value=deserialize_value(data["value"]),
            data_type=data["data_type"],
            source=data["source"],
            timestamp=data["timestamp"],
            trace_id=data.get("trace_id"),
            observation_id=data.get("observation_id"),
            comment=data.get("comment"),
        )


@dataclass(frozen=True)
class AttemptRecord:
    model: str | Unavailable
    provider: str | Unavailable
    status: Status
    error_message: str | None
    latency_ms: int
    prompt_tokens: int | Unavailable
    completion_tokens: int | Unavailable
    total_tokens: int | Unavailable
    cost_usd: float | Unavailable


@dataclass(frozen=True)
class FallbackEvidence:
    primary: AttemptRecord
    fallback: AttemptRecord
    simulated: bool


@dataclass(frozen=True)
class RepeatObservation:
    first: StreamedResult
    second: StreamedResult
    cache_status: str | Unavailable
    cached_tokens: int | Unavailable
    cache_write_tokens: int | Unavailable


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
    fallback_evidence: FallbackEvidence | None = None
    repeat_observation: RepeatObservation | None = None
