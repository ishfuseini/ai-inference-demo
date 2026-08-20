import asyncio
from collections.abc import AsyncIterator

from openrouter_demo.models import (
    UNAVAILABLE,
    RepeatObservation,
    StreamChunk,
    StreamedResult,
)
from openrouter_demo.routing import DEFAULT_STRATEGY
from openrouter_demo.scenarios import run_repeat_scenario


def _collect_events(stream: object, prompt: str = "test prompt") -> list[object]:
    async def _run() -> list[object]:
        events: list[object] = []
        async for event in run_repeat_scenario(
            prompt,
            strategy=DEFAULT_STRATEGY,
            api_key="sk-test",
            stream_fn=stream,
        ):
            events.append(event)
        return events

    return asyncio.run(_run())


def test_repeat_scenario_reports_cache_hit_from_run_2() -> None:
    call_count = 0

    async def stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            yield StreamedResult(
                text="first",
                model="openai/gpt-4o-mini",
                provider="OpenAI",
                prompt_tokens=5,
                completion_tokens=3,
                total_tokens=8,
                cost_usd=0.006,
                latency_ms=300,
            )
        else:
            yield StreamChunk("second")
            yield StreamedResult(
                text="second",
                model="openai/gpt-4o-mini",
                provider="OpenAI",
                prompt_tokens=5,
                completion_tokens=3,
                total_tokens=8,
                cost_usd=0.004,
                latency_ms=180,
                cache_status="hit",
                cached_tokens=10,
                cache_write_tokens=0,
            )

    events = _collect_events(stream)
    obs = events[-1]
    assert isinstance(obs, RepeatObservation)
    assert obs.cache_status == "hit"
    assert obs.cached_tokens == 10
    assert obs.first is not None
    assert obs.second is not None


def test_repeat_scenario_reports_absent_cache_with_latency_and_cost() -> None:
    call_count = 0

    async def stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            yield StreamedResult(
                text="first",
                model="openai/gpt-4o-mini",
                provider="OpenAI",
                prompt_tokens=5,
                completion_tokens=3,
                total_tokens=8,
                cost_usd=0.006,
                latency_ms=300,
            )
        else:
            yield StreamedResult(
                text="second",
                model="openai/gpt-4o-mini",
                provider="OpenAI",
                prompt_tokens=5,
                completion_tokens=3,
                total_tokens=8,
                cost_usd=0.004,
                latency_ms=180,
            )

    events = _collect_events(stream)
    obs = events[-1]
    assert isinstance(obs, RepeatObservation)
    assert obs.cache_status is UNAVAILABLE
    assert obs.first.latency_ms == 300
    assert obs.second.latency_ms == 180
    assert obs.first.cost_usd == 0.006
    assert obs.second.cost_usd == 0.004


def test_repeat_scenario_yields_only_run_2_chunks() -> None:
    call_count = 0

    async def stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            yield StreamChunk("first-chunk")
            yield StreamedResult(
                text="first",
                model="openai/gpt-4o-mini",
                provider="OpenAI",
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                cost_usd=0.001,
                latency_ms=10,
            )
        else:
            yield StreamChunk("second-a")
            yield StreamChunk("second-b")
            yield StreamedResult(
                text="second",
                model="openai/gpt-4o-mini",
                provider="OpenAI",
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                cost_usd=0.001,
                latency_ms=10,
            )

    events = _collect_events(stream)
    chunks = [e for e in events if isinstance(e, StreamChunk)]
    assert [c.text_delta for c in chunks] == ["second-a", "second-b"]


def test_repeat_scenario_cache_derives_only_from_run_2() -> None:
    call_count = 0

    async def stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            yield StreamedResult(
                text="first",
                model="openai/gpt-4o-mini",
                provider="OpenAI",
                prompt_tokens=5,
                completion_tokens=3,
                total_tokens=8,
                cost_usd=0.006,
                latency_ms=300,
                cache_status="hit",
                cached_tokens=99,
                cache_write_tokens=0,
            )
        else:
            yield StreamedResult(
                text="second",
                model="openai/gpt-4o-mini",
                provider="OpenAI",
                prompt_tokens=5,
                completion_tokens=3,
                total_tokens=8,
                cost_usd=0.004,
                latency_ms=180,
            )

    events = _collect_events(stream)
    obs = events[-1]
    assert isinstance(obs, RepeatObservation)
    assert obs.cache_status is UNAVAILABLE
    assert obs.cached_tokens is UNAVAILABLE


def test_repeat_types_importable_without_circular_import() -> None:
    from openrouter_demo.models import RepeatObservation as _RO
    from openrouter_demo.scenarios import run_repeat_scenario as _rrs

    assert _RO is RepeatObservation
    assert callable(_rrs)
