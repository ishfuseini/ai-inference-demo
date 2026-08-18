from dataclasses import dataclass

from openrouter_demo.config import AppConfig


@dataclass(frozen=True)
class TraceReadiness:
    enabled: bool
    detail: str


def trace_readiness_from_config(config: AppConfig) -> TraceReadiness:
    if config.langfuse_ready:
        return TraceReadiness(enabled=True, detail="Langfuse credentials are configured.")
    return TraceReadiness(enabled=False, detail="Langfuse tracing disabled; optional env vars are incomplete.")
