import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from openrouter_demo.client import OpenRouterHTTPError
from openrouter_demo.history import RunHistory
from openrouter_demo.models import (
    UNAVAILABLE,
    AttemptRecord,
    FallbackEvidence,
    InferenceRun,
    Status,
    StreamChunk,
    StreamedResult,
    TelemetryEvidence,
)
from openrouter_demo.routing import COST_STRATEGY, DEFAULT_STRATEGY, LATENCY_STRATEGY, STRATEGIES
from openrouter_demo.ui import (
    FALLBACK_SUCCESS_RESPONSE,
    STREAMING_RESPONSE,
    _format_cost,
    _format_metadata,
    _history_rows,
    _run_inference,
    _telemetry_rows,
)


def _run(coro):
    return asyncio.run(coro)


def test_run_inference_records_successful_stream() -> None:
    async def fake_stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
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
    run = _run(
        _run_inference(
            "Explain streaming", api_key="sk-test", history=history, stream_fn=fake_stream
        )
    )

    assert run.status is Status.SUCCEEDED
    assert run.streamed_text == "Hello there"
    assert run.strategy_name == DEFAULT_STRATEGY.name
    assert run.telemetry is not None
    assert run.telemetry.model == "openai/gpt-4o-mini"
    assert run.telemetry.provider == "OpenAI"
    assert run.telemetry.latency_ms == 321
    assert history.all() == [run]


def test_run_inference_preserves_unavailable_metadata() -> None:
    async def fake_stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
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

    run = _run(
        _run_inference("Prompt", api_key="sk-test", history=RunHistory(), stream_fn=fake_stream)
    )

    assert run.telemetry is not None
    assert run.telemetry.model is UNAVAILABLE
    assert run.telemetry.provider is UNAVAILABLE
    assert run.telemetry.prompt_tokens is UNAVAILABLE
    assert run.telemetry.cost_usd is UNAVAILABLE
    assert _format_metadata(UNAVAILABLE) == "Unavailable from selected route/provider."
    assert _format_cost(UNAVAILABLE) == "Cost metadata was not returned for this route/provider."


def test_run_inference_records_partial_text_on_stream_failure() -> None:
    async def fake_stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
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
    async def fake_stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        raise AssertionError("blank prompts must not start a request")

    try:
        _run(_run_inference("  ", api_key="sk-test", history=RunHistory(), stream_fn=fake_stream))
    except ValueError as exc:
        assert str(exc) == "Prompt must not be blank."
    else:
        raise AssertionError("blank prompt was accepted")


def test_telemetry_and_history_rows_render_unavailable_copy() -> None:
    run = InferenceRun(
        run_id="run-1",
        prompt="Prompt",
        strategy_name=DEFAULT_STRATEGY.name,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        status=Status.SUCCEEDED,
        streamed_text="done",
        error_message=None,
        telemetry=TelemetryEvidence(
            model=UNAVAILABLE,
            provider=UNAVAILABLE,
            latency_ms=15,
            prompt_tokens=UNAVAILABLE,
            completion_tokens=UNAVAILABLE,
            total_tokens=UNAVAILABLE,
            cost_usd=UNAVAILABLE,
        ),
    )
    history = RunHistory()
    history.append(run)

    telemetry = dict(_telemetry_rows(run))
    assert telemetry["Model"] == "Unavailable from selected route/provider."
    assert telemetry["Provider"] == "Unavailable from selected route/provider."
    assert telemetry["Tokens"] == "Unavailable from selected route/provider."
    assert telemetry["Cost"] == "Cost metadata was not returned for this route/provider."
    assert _history_rows(history)[0][2:] == (
        "Unavailable from selected route/provider.",
        "Unavailable from selected route/provider.",
        "15 ms",
        "Unavailable from selected route/provider.",
        "Cost metadata was not returned for this route/provider.",
        "—",
    )


def test_telemetry_rows_reflect_run_strategy() -> None:
    run = InferenceRun(
        run_id="run-strategy",
        prompt="Prompt",
        strategy_name="cost",
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        status=Status.SUCCEEDED,
        streamed_text="done",
        error_message=None,
        telemetry=None,
    )

    telemetry = dict(_telemetry_rows(run))
    assert telemetry["Strategy"] == "cost"

    idle = dict(_telemetry_rows(None))
    assert idle["Strategy"] == DEFAULT_STRATEGY.name
    assert idle["Latency"] == "Latency was not returned for this route/provider."
    assert idle["Tokens"] == "Unavailable from selected route/provider."


def test_telemetry_rows_streaming_state_copy() -> None:
    rows = dict(_telemetry_rows(None, is_running=True))
    assert rows["Status"] == STREAMING_RESPONSE
    assert rows["Latency"] == "Latency was not returned for this route/provider."


def test_run_inference_records_cost_strategy_name() -> None:
    async def fake_stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        yield StreamedResult(
            text="done",
            model="openai/gpt-4o-mini",
            provider="OpenAI",
            prompt_tokens=3,
            completion_tokens=4,
            total_tokens=7,
            cost_usd=0.001,
            latency_ms=200,
        )

    run = _run(
        _run_inference(
            "Prompt",
            api_key="sk-test",
            history=RunHistory(),
            stream_fn=fake_stream,
            strategy=COST_STRATEGY,
        )
    )
    assert run.strategy_name == "cost"


def test_run_inference_records_latency_strategy_name() -> None:
    async def fake_stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        yield StreamedResult(
            text="done",
            model="openai/gpt-4o-mini",
            provider="OpenAI",
            prompt_tokens=3,
            completion_tokens=4,
            total_tokens=7,
            cost_usd=0.001,
            latency_ms=100,
        )

    run = _run(
        _run_inference(
            "Prompt",
            api_key="sk-test",
            history=RunHistory(),
            stream_fn=fake_stream,
            strategy=LATENCY_STRATEGY,
        )
    )
    assert run.strategy_name == "latency"


def test_strategies_dict_contains_three_selectable_strategies() -> None:
    assert set(STRATEGIES.keys()) == {"default", "cost", "latency"}


def test_history_rows_include_fallback_column() -> None:
    run = InferenceRun(
        run_id="run-1",
        prompt="Prompt",
        strategy_name=DEFAULT_STRATEGY.name,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        status=Status.SUCCEEDED,
        streamed_text="done",
        error_message=None,
        telemetry=TelemetryEvidence(
            model="openai/gpt-4o-mini",
            provider="OpenAI",
            latency_ms=200,
            prompt_tokens=3,
            completion_tokens=4,
            total_tokens=7,
            cost_usd=0.001,
        ),
    )
    history = RunHistory()
    history.append(run)

    rows = _history_rows(history)
    assert len(rows[0]) == 8
    assert rows[0][-1] == "—"

    primary = AttemptRecord(
        model="nonexistent/fake-model-for-demo",
        provider=UNAVAILABLE,
        status=Status.FAILED,
        error_message="OpenRouter request failed (404)",
        latency_ms=12,
        prompt_tokens=UNAVAILABLE,
        completion_tokens=UNAVAILABLE,
        total_tokens=UNAVAILABLE,
        cost_usd=UNAVAILABLE,
    )
    fallback = AttemptRecord(
        model="openai/gpt-4o-mini",
        provider="OpenAI",
        status=Status.SUCCEEDED,
        error_message=None,
        latency_ms=200,
        prompt_tokens=3,
        completion_tokens=4,
        total_tokens=7,
        cost_usd=0.001,
    )
    fallback_run = InferenceRun(
        run_id="run-2",
        prompt="Prompt",
        strategy_name=DEFAULT_STRATEGY.name,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        status=Status.FALLBACK_SUCCEEDED,
        streamed_text="Fallback response",
        error_message=None,
        telemetry=TelemetryEvidence(
            model="openai/gpt-4o-mini",
            provider="OpenAI",
            latency_ms=200,
            prompt_tokens=3,
            completion_tokens=4,
            total_tokens=7,
            cost_usd=0.001,
        ),
        fallback_evidence=FallbackEvidence(primary=primary, fallback=fallback, simulated=True),
    )
    history.append(fallback_run)
    rows = _history_rows(history)
    assert rows[1][-1] == "Yes"


def test_telemetry_rows_fallback_success_status() -> None:
    primary = AttemptRecord(
        model="nonexistent/fake-model-for-demo",
        provider=UNAVAILABLE,
        status=Status.FAILED,
        error_message="OpenRouter request failed (404)",
        latency_ms=12,
        prompt_tokens=UNAVAILABLE,
        completion_tokens=UNAVAILABLE,
        total_tokens=UNAVAILABLE,
        cost_usd=UNAVAILABLE,
    )
    fallback = AttemptRecord(
        model="openai/gpt-4o-mini",
        provider="OpenAI",
        status=Status.SUCCEEDED,
        error_message=None,
        latency_ms=200,
        prompt_tokens=3,
        completion_tokens=4,
        total_tokens=7,
        cost_usd=0.001,
    )
    run = InferenceRun(
        run_id="run-fb",
        prompt="Prompt",
        strategy_name=DEFAULT_STRATEGY.name,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        status=Status.FALLBACK_SUCCEEDED,
        streamed_text="Fallback response",
        error_message=None,
        telemetry=TelemetryEvidence(
            model="openai/gpt-4o-mini",
            provider="OpenAI",
            latency_ms=200,
            prompt_tokens=3,
            completion_tokens=4,
            total_tokens=7,
            cost_usd=0.001,
        ),
        fallback_evidence=FallbackEvidence(primary=primary, fallback=fallback, simulated=True),
    )

    rows = dict(_telemetry_rows(run))
    assert rows["Status"] == FALLBACK_SUCCESS_RESPONSE
