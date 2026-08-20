from __future__ import annotations

import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass

from openrouter_demo.client import OpenRouterError, stream_chat_completion
from openrouter_demo.models import (
    UNAVAILABLE,
    AttemptRecord,
    Status,
    StreamChunk,
    StreamedResult,
)
from openrouter_demo.routing import FALLBACK_PRIMARY_STRATEGY, RoutingStrategy

type StreamFn = Callable[..., AsyncIterator[StreamChunk | StreamedResult]]


class PhaseNotImplementedError(NotImplementedError):
    pass


@dataclass(frozen=True)
class FallbackResult:
    primary: AttemptRecord
    fallback: StreamedResult | None
    simulated: bool


async def run_fallback_scenario(
    prompt: str,
    *,
    fallback_strategy: RoutingStrategy,
    api_key: str,
    stream_fn: StreamFn = stream_chat_completion,
) -> AsyncIterator[StreamChunk | FallbackResult]:
    # Attempt 1: primary (deterministic failure)
    primary_error: OpenRouterError | None = None
    primary_start = time.monotonic()
    try:
        async for _event in stream_fn(
            prompt,
            strategy=FALLBACK_PRIMARY_STRATEGY,
            api_key=api_key,
        ):
            pass  # primary should fail before yielding any chunks
    except OpenRouterError as exc:
        primary_error = exc

    primary_record = AttemptRecord(
        model=FALLBACK_PRIMARY_STRATEGY.model,
        provider=UNAVAILABLE,
        status=Status.FAILED if primary_error is not None else Status.SUCCEEDED,
        error_message=str(primary_error) if primary_error is not None else None,
        latency_ms=int((time.monotonic() - primary_start) * 1000),
        prompt_tokens=UNAVAILABLE,
        completion_tokens=UNAVAILABLE,
        total_tokens=UNAVAILABLE,
        cost_usd=UNAVAILABLE,
    )

    if primary_error is None:
        # Edge case: primary unexpectedly succeeded — treat as normal run
        yield FallbackResult(primary=primary_record, fallback=None, simulated=True)
        return

    # Attempt 2: fallback (real strategy, should succeed)
    fallback_result: StreamedResult | None = None
    async for event in stream_fn(
        prompt,
        strategy=fallback_strategy,
        api_key=api_key,
    ):
        if isinstance(event, StreamChunk):
            yield event  # stream chunks to UI for progressive display
        elif isinstance(event, StreamedResult):
            fallback_result = event

    # Yield combined fallback result with both attempt records
    yield FallbackResult(
        primary=primary_record,
        fallback=fallback_result,
        simulated=True,
    )
