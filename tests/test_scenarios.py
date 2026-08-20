import asyncio
from collections.abc import AsyncIterator

from openrouter_demo.client import OpenRouterHTTPError
from openrouter_demo.models import UNAVAILABLE, Status, StreamChunk, StreamedResult
from openrouter_demo.routing import DEFAULT_STRATEGY, FALLBACK_PRIMARY_STRATEGY
from openrouter_demo.scenarios import FallbackResult, run_fallback_scenario


def _dual_stream() -> object:
    call_count = 0

    async def stream(*_args: object, **_kwargs: object) -> AsyncIterator[StreamChunk | StreamedResult]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OpenRouterHTTPError(
                "OpenRouter request failed (404)", status_code=404, partial_text=""
            )
        yield StreamChunk("Fallback ")
        yield StreamChunk("response")
        yield StreamedResult(
            text="Fallback response",
            model="openai/gpt-4o-mini",
            provider="OpenAI",
            prompt_tokens=3,
            completion_tokens=4,
            total_tokens=7,
            cost_usd=0.001,
            latency_ms=200,
        )

    return stream


def _collect_events(stream: object) -> list[object]:
    async def _run() -> list[object]:
        events: list[object] = []
        async for event in run_fallback_scenario(
            "test prompt",
            fallback_strategy=DEFAULT_STRATEGY,
            api_key="sk-test",
            stream_fn=stream,
        ):
            events.append(event)
        return events

    return asyncio.run(_run())


def test_fallback_scenario_primary_fails_fallback_succeeds() -> None:
    events = _collect_events(_dual_stream())
    result = events[-1]
    assert isinstance(result, FallbackResult)
    assert result.primary.status is Status.FAILED
    assert "404" in result.primary.error_message
    assert result.primary.model == "nonexistent/fake-model-for-demo"
    assert result.primary.model == FALLBACK_PRIMARY_STRATEGY.model
    assert result.primary.provider is UNAVAILABLE
    assert result.fallback is not None
    assert result.fallback.model == "openai/gpt-4o-mini"
    assert result.fallback.provider == "OpenAI"
    assert result.simulated is True


def test_fallback_scenario_yields_stream_chunks_progressively() -> None:
    events = _collect_events(_dual_stream())
    chunks = [e for e in events if isinstance(e, StreamChunk)]
    assert len(chunks) == 2
    assert chunks[0].text_delta == "Fallback "
    assert chunks[1].text_delta == "response"


def test_fallback_scenario_primary_latency_is_non_negative() -> None:
    events = _collect_events(_dual_stream())
    result = events[-1]
    assert isinstance(result, FallbackResult)
    assert result.primary.latency_ms >= 0


def test_fallback_scenario_primary_unexpectedly_succeeds() -> None:
    async def succeeding_stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        yield StreamedResult(
            text="Primary succeeded unexpectedly",
            model="openai/gpt-4o-mini",
            provider="OpenAI",
            prompt_tokens=3,
            completion_tokens=4,
            total_tokens=7,
            cost_usd=0.001,
            latency_ms=100,
        )

    async def _run() -> list[object]:
        events: list[object] = []
        async for event in run_fallback_scenario(
            "test prompt",
            fallback_strategy=DEFAULT_STRATEGY,
            api_key="sk-test",
            stream_fn=succeeding_stream,
        ):
            events.append(event)
        return events

    events = asyncio.run(_run())
    result = events[-1]
    assert isinstance(result, FallbackResult)
    assert result.primary.status is Status.SUCCEEDED
    assert result.fallback is None
