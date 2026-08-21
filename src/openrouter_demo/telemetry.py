from dataclasses import dataclass

from openrouter_demo.config import AppConfig


@dataclass(frozen=True)
class TraceOutcome:
    status: str  # "enabled" | "disabled" | "failed"
    trace_id: str | None
    trace_url: str | None


def record_trace(
    config: AppConfig,
    *,
    name: str,
    model: str,
    input: dict,
    output: str,
    usage_details: dict[str, int],
) -> TraceOutcome:
    if not config.langfuse_ready:
        return TraceOutcome(status="disabled", trace_id=None, trace_url=None)
    try:
        from langfuse import get_client

        client = get_client()
        with client.start_as_current_observation(
            name=name,
            as_type="generation",
            model=model,
            input=input,
            output=output,
            usage_details=usage_details,
        ) as gen:
            trace_id = gen.trace_id
        client.flush()
        return TraceOutcome(
            status="enabled",
            trace_id=trace_id,
            trace_url=client.get_trace_url(trace_id=trace_id),
        )
    except Exception:  # noqa: BLE001 — tracing must never block or break inference
        return TraceOutcome(status="failed", trace_id=None, trace_url=None)
