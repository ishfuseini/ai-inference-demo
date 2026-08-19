import asyncio
from collections.abc import AsyncIterator

from openrouter_demo.client import OpenRouterHTTPError
from openrouter_demo.history import RunHistory
from openrouter_demo.models import UNAVAILABLE, Status, StreamChunk, StreamedResult
from openrouter_demo.routing import DEFAULT_STRATEGY
from openrouter_demo.ui import _format_cost, _format_metadata, _run_inference


def _run(coro):
    return asyncio.run(coro)


def test_run_inference_records_successful_stream() -> None:
    async def fake_stream(*_args: object, **_kwargs: object) -> AsyncIterator[StreamChunk | StreamedResult]:
        yield StreamChunk("Hello ")
        yield StreamChunk("there")
        yield StreamedResult(
            text="Hello there",
            model="openai/gpt-4o-mini",
            provider="OpenAI",
            prompt_tokens=3,
            completion_tokens=4,
            total_tokens=7,
            cost_usd=0.001,
            latency_ms=321,
        )

    history = RunHistory()
    run = _run(_run_inference("Explain streaming", api_key="sk-test", history=history, stream_fn=fake_stream))

    assert run.status is Status.SUCCEEDED
    assert run.streamed_text == "Hello there"
    assert run.strategy_name == DEFAULT_STRATEGY.name
    assert run.telemetry is not None
    assert run.telemetry.model == "openai/gpt-4o-mini"
    assert run.telemetry.provider == "OpenAI"
    assert run.telemetry.latency_ms == 321
    assert history.all() == [run]


def test_run_inference_preserves_unavailable_metadata() -> None:
    async def fake_stream(*_args: object, **_kwargs: object) -> AsyncIterator[StreamChunk | StreamedResult]:
        yield StreamedResult(
            text="done",
            model=UNAVAILABLE,
            provider=UNAVAILABLE,
            prompt_tokens=UNAVAILABLE,
            completion_tokens=UNAVAILABLE,
            total_tokens=UNAVAILABLE,
            cost_usd=UNAVAILABLE,
            latency_ms=12,
        )

    run = _run(_run_inference("Prompt", api_key="sk-test", history=RunHistory(), stream_fn=fake_stream))

    assert run.telemetry is not None
    assert run.telemetry.model is UNAVAILABLE
    assert run.telemetry.provider is UNAVAILABLE
    assert run.telemetry.prompt_tokens is UNAVAILABLE
    assert run.telemetry.cost_usd is UNAVAILABLE
    assert _format_metadata(UNAVAILABLE) == "Unavailable from selected route/provider."
    assert _format_cost(UNAVAILABLE) == "Cost metadata was not returned for this route/provider."


def test_run_inference_records_partial_text_on_stream_failure() -> None:
    async def fake_stream(*_args: object, **_kwargs: object) -> AsyncIterator[StreamChunk | StreamedResult]:
        yield StreamChunk("partial")
        raise OpenRouterHTTPError("provider failed", status_code=500, partial_text="partial")

    history = RunHistory()
    run = _run(_run_inference("Prompt", api_key="sk-test", history=history, stream_fn=fake_stream))

    assert run.status is Status.FAILED
    assert run.error_message == "provider failed"
    assert run.streamed_text == "partial"
    assert run.telemetry is None
    assert history.all() == [run]


def test_run_inference_rejects_blank_prompt() -> None:
    async def fake_stream(*_args: object, **_kwargs: object) -> AsyncIterator[StreamChunk | StreamedResult]:
        raise AssertionError("blank prompts must not start a request")

    try:
        _run(_run_inference("  ", api_key="sk-test", history=RunHistory(), stream_fn=fake_stream))
    except ValueError as exc:
        assert str(exc) == "Prompt must not be blank."
    else:
        raise AssertionError("blank prompt was accepted")
