import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

from openrouter_demo.client import OpenRouterHTTPError
from openrouter_demo.config import load_config
from openrouter_demo.sqlite_store import SQLiteRunHistory
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
from openrouter_demo.routing import (
    COST_STRATEGY,
    DEFAULT_STRATEGY,
    LATENCY_STRATEGY,
    STRATEGIES,
)
from openrouter_demo.ui import (
    EVAL_DESCRIPTION,
    EVAL_SCORING_ROWS,
    SAMPLE_PROMPTS,
    STRATEGY_MODEL_OPTIONS,
    STREAMING_RESPONSE,
    SUCCESS_RESPONSE,
    _comparison_rows,
    _format_cost,
    _format_metadata,
    _history_rows,
    _history_trace_href,
    _run_fallback_inference,
    _run_inference,
    _strategy_with_model,
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

    history = SQLiteRunHistory(db_path=":memory:")
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
        _run_inference("Prompt", api_key="sk-test", history=SQLiteRunHistory(db_path=":memory:"), stream_fn=fake_stream)
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

    history = SQLiteRunHistory(db_path=":memory:")
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
        _run(_run_inference("  ", api_key="sk-test", history=SQLiteRunHistory(db_path=":memory:"), stream_fn=fake_stream))
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
    history = SQLiteRunHistory(db_path=":memory:")
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
        "Unavailable from selected route/provider.",
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
    assert idle["Strategy"] == "Waiting"
    assert idle["Model"] == "Waiting"
    assert idle["Provider"] == "Waiting"
    assert idle["Latency"] == "Waiting"
    assert idle["Tokens"] == "Waiting"
    assert idle["Cost"] == "Waiting"
    assert idle["Router"] == "Waiting"
    assert idle["Trace"] == "Waiting"


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
            history=SQLiteRunHistory(db_path=":memory:"),
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
            history=SQLiteRunHistory(db_path=":memory:"),
            stream_fn=fake_stream,
            strategy=LATENCY_STRATEGY,
        )
    )
    assert run.strategy_name == "latency"


def test_strategies_dict_contains_three_selectable_strategies() -> None:
    assert set(STRATEGIES.keys()) == {"cost", "latency", "intelligence"}


def test_strategy_with_model_preserves_routing_preferences() -> None:
    strategy = _strategy_with_model(COST_STRATEGY, "mistralai/mistral-nemo")

    assert strategy.name == COST_STRATEGY.name
    assert strategy.description == COST_STRATEGY.description
    assert strategy.provider_preferences == COST_STRATEGY.provider_preferences
    assert strategy.model == "mistralai/mistral-nemo"
    assert COST_STRATEGY.model == DEFAULT_STRATEGY.model


def test_strategy_model_options_are_hard_coded_by_strategy() -> None:
    assert STRATEGY_MODEL_OPTIONS == {
        "cost": {
            "nvidia/nemotron-3.5-lightning:free": "nvidia/nemotron-3.5-lightning:free",
            "google/gemma-4-31b-it:free": "google/gemma-4-31b-it:free",
            "openai/gpt-oss-20b:free": "openai/gpt-oss-20b:free",
        },
        "latency": {
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free": (
                "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
            ),
            "poolside/laguna-xs-2.1:free": "poolside/laguna-xs-2.1:free",
            "google/gemma-4-26b-a4b-it:free": "google/gemma-4-26b-a4b-it:free",
        },
        "intelligence": {
            "anthropic/claude-opus-5": "anthropic/claude-opus-5",
            "openai/gpt-5.6-sol": "openai/gpt-5.6-sol",
            "moonshotai/kimi-k3": "moonshotai/kimi-k3",
        },
    }
    assert set(STRATEGY_MODEL_OPTIONS) == set(STRATEGIES)
    assert all(len(options) == 3 for options in STRATEGY_MODEL_OPTIONS.values())
    assert all(label == model_id for options in STRATEGY_MODEL_OPTIONS.values() for model_id, label in options.items())


def test_history_rows_show_trace_without_fallback_or_cache_columns() -> None:
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
    history = SQLiteRunHistory(db_path=":memory:")
    history.append(run)

    rows = _history_rows(history)
    assert len(rows[0]) == 8
    assert rows[0][-1] == "Unavailable from selected route/provider."

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
    assert len(rows[1]) == 8
    assert "Yes" not in rows[1]


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
    assert rows["Status"] == SUCCESS_RESPONSE


def test_run_fallback_inference_produces_fallback_succeeded_run() -> None:
    call_count = 0

    async def dual_stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
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

    run = _run(
        _run_fallback_inference(
            "test",
            api_key="sk-test",
            history=SQLiteRunHistory(db_path=":memory:"),
            fallback_strategy=DEFAULT_STRATEGY,
            stream_fn=dual_stream,
        )
    )

    assert run.status is Status.FALLBACK_SUCCEEDED
    assert run.fallback_evidence is not None
    assert run.fallback_evidence.primary.status is Status.FAILED
    assert run.fallback_evidence.fallback.status is Status.SUCCEEDED
    assert run.streamed_text == "Fallback response"
    assert run.telemetry is not None
    assert run.telemetry.model == "openai/gpt-4o-mini"
    assert run.telemetry.provider == "OpenAI"


def test_telemetry_rows_render_fallback_evidence() -> None:
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
        run_id="run-fb-evidence",
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
    assert rows["Status"] == SUCCESS_RESPONSE
    assert "Primary status" not in rows
    assert "Fallback model" not in rows


def test_run_inference_without_config_skips_tracing() -> None:
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
        _run_inference("Prompt", api_key="sk-test", history=SQLiteRunHistory(db_path=":memory:"), stream_fn=fake_stream)
    )
    assert run.status is Status.SUCCEEDED
    assert run.telemetry is not None
    assert run.telemetry.trace_status is UNAVAILABLE
    assert run.telemetry.trace_id is None


def test_run_inference_with_langfuse_disabled_config_records_trace_status() -> None:
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
            history=SQLiteRunHistory(db_path=":memory:"),
            stream_fn=fake_stream,
            config=load_config({}),
        )
    )
    assert run.status is Status.SUCCEEDED
    assert run.telemetry is not None
    assert run.telemetry.trace_status == "disabled"
    assert run.telemetry.trace_id is None


def _fallback_stream_for_ui_test() -> object:
    call_count = 0

    async def dual_stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OpenRouterHTTPError(
                "OpenRouter request failed (404)", status_code=404, partial_text=""
            )
        yield StreamChunk("Fallback ")
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

    return dual_stream


def test_run_fallback_inference_without_config_skips_tracing() -> None:
    run = _run(
        _run_fallback_inference(
            "test",
            api_key="sk-test",
            history=SQLiteRunHistory(db_path=":memory:"),
            fallback_strategy=DEFAULT_STRATEGY,
            stream_fn=_fallback_stream_for_ui_test(),
        )
    )
    assert run.status is Status.FALLBACK_SUCCEEDED
    assert run.telemetry is not None
    assert run.telemetry.trace_status is UNAVAILABLE
    assert run.telemetry.trace_id is None


def test_run_fallback_inference_with_langfuse_disabled_config_records_trace_status() -> None:
    run = _run(
        _run_fallback_inference(
            "test",
            api_key="sk-test",
            history=SQLiteRunHistory(db_path=":memory:"),
            fallback_strategy=DEFAULT_STRATEGY,
            stream_fn=_fallback_stream_for_ui_test(),
            config=load_config({}),
        )
    )
    assert run.status is Status.FALLBACK_SUCCEEDED
    assert run.telemetry is not None
    assert run.telemetry.trace_status == "disabled"
    assert run.telemetry.trace_id is None


def test_history_rows_render_trace_status_and_link_target() -> None:
    run = InferenceRun(
        run_id="run-cache-trace",
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
            trace_status="enabled",
            trace_id="abc123",
            trace_url="https://cloud.langfuse.com/traces/abc123",
        ),
    )
    history = SQLiteRunHistory(db_path=":memory:")
    history.append(run)
    rows = _history_rows(history)
    assert len(rows[0]) == 8
    assert rows[0][-1] == "https://cloud.langfuse.com/traces/abc123"
    assert _history_trace_href(run) == "https://cloud.langfuse.com/traces/abc123"


def test_comparison_rows_include_completed_runs() -> None:
    def _run(model: str, status: Status, completed: bool = True) -> InferenceRun:
        return InferenceRun(
            run_id=f"run-{model}",
            prompt="Prompt",
            strategy_name=DEFAULT_STRATEGY.name,
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC) if completed else None,
            status=status,
            streamed_text="done",
            error_message=None,
            telemetry=TelemetryEvidence(
                model=model,
                provider="OpenAI",
                latency_ms=200,
                prompt_tokens=3,
                completion_tokens=4,
                total_tokens=7,
                cost_usd=0.001,
            ),
        )

    history = SQLiteRunHistory(db_path=":memory:")
    history.append(_run("openai/gpt-4o-mini", Status.SUCCEEDED))
    history.append(_run("openai/gpt-4o-mini-extra", Status.SUCCEEDED))
    history.append(_run("failed-model", Status.FAILED))
    history.append(_run("pending-model", Status.PENDING, completed=False))

    rows_all = _comparison_rows(history)
    models_all = [row[1] for row in rows_all]
    assert len(rows_all) >= 2
    assert rows_all[0][0] == "1"
    assert rows_all[1][0] == "2"
    assert "openai/gpt-4o-mini" in models_all
    assert "openai/gpt-4o-mini-extra" in models_all
    assert "failed-model" not in models_all
    assert "pending-model" not in models_all

    rows_limited = _comparison_rows(history, limit=1)
    assert len(rows_limited) == 1

    # Trace labels in comparison rows must match history rows; trace URL also powers run links.
    trace_run = InferenceRun(
        run_id="run-compare-trace",
        prompt="Prompt trace",
        strategy_name=DEFAULT_STRATEGY.name,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        status=Status.SUCCEEDED,
        streamed_text="trace done",
        error_message=None,
        telemetry=TelemetryEvidence(
            model="openai/gpt-4o-mini-trace",
            provider="OpenAI",
            latency_ms=250,
            prompt_tokens=4,
            completion_tokens=5,
            total_tokens=9,
            cost_usd=0.0015,
            trace_status="enabled",
            trace_id="abc123",
            trace_url="https://cloud.langfuse.com/traces/abc123",
        ),
    )
    trace_history = SQLiteRunHistory(db_path=":memory:")
    trace_history.append(trace_run)

    history_rows = _history_rows(trace_history)
    comparison_rows = _comparison_rows(trace_history)
    assert len(history_rows) == 1
    assert len(comparison_rows) == 1
    assert comparison_rows[0][-1] == history_rows[0][-1]
    assert comparison_rows[0][-1] == "https://cloud.langfuse.com/traces/abc123"
    assert _history_trace_href(trace_run) == "https://cloud.langfuse.com/traces/abc123"


def test_run_fallback_inference_appends_to_history() -> None:
    call_count = 0

    async def dual_stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OpenRouterHTTPError(
                "OpenRouter request failed (404)", status_code=404, partial_text=""
            )
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

    history = SQLiteRunHistory(db_path=":memory:")
    run = _run(
        _run_fallback_inference(
            "test",
            api_key="sk-test",
            history=history,
            fallback_strategy=DEFAULT_STRATEGY,
            stream_fn=dual_stream,
        )
    )
    assert history.all() == [run]


def test_ui_has_no_chatbot_labels() -> None:
    text = Path("src/openrouter_demo/ui.py").read_text()
    for inference_copy in (
        'ui.page_title("ishlab Production Inference Lab")',
        '_heading("Production Inference Lab", level=1, classes="demo-page-title")',
        "The app runs live streaming inference",
        "This demo shows what changes when inference becomes something you have to operate",
        'ui.button("Run Inference", on_click=run_request)',
        '"LLM Response"',
        '"Model"',
        '"Choose one of the three hard-coded models for the selected strategy."',
        "demo-prompt-card",
        "rows=18",
        "demo-response-output",
        '"Telemetry"',
        '"Run history"',
        '"Comparison"',
    ):
        assert inference_copy in text
    for forbidden in (
        "ui.chat_message",
        '"assistant"',
        '"user"',
        "Chat",
        "Send message",
    ):
        assert forbidden not in text


def test_sample_prompt_buttons_have_short_labels_and_full_prompts() -> None:
    text = Path("src/openrouter_demo/ui.py").read_text()

    assert "ui.button(" in text
    assert "sample.label" in text
    assert "fill_prompt(sample.prompt)" in text
    assert all(sample.label != sample.prompt for sample in SAMPLE_PROMPTS)
    assert all(len(sample.label) <= 32 for sample in SAMPLE_PROMPTS)
    assert any("launch-window impact" in sample.prompt for sample in SAMPLE_PROMPTS)
    assert any("at least two concrete diagnostics" in sample.prompt for sample in SAMPLE_PROMPTS)
    assert any("renewal risk directly" in sample.prompt for sample in SAMPLE_PROMPTS)
    assert any("something concrete they can take to their CTO" in sample.prompt for sample in SAMPLE_PROMPTS)


def test_prompt_panel_describes_eval_rubric() -> None:
    text = Path("src/openrouter_demo/ui.py").read_text()

    assert "ui.html(EVAL_DESCRIPTION)" in text
    assert "_render_eval_scoring_table()" in text
    assert "API keeps failing" in EVAL_DESCRIPTION
    assert "Leads with the customer's problem" in EVAL_DESCRIPTION
    assert "Asks for real detail" in EVAL_DESCRIPTION
    assert "Commits to a next step" in EVAL_DESCRIPTION
    assert any("ACK, NODEF, DIAG, NEXT" in row[1] for row in EVAL_SCORING_ROWS)
    assert any(row[0] == "Tone score" for row in EVAL_SCORING_ROWS)
    assert any(row[0] == "Auto-fail" for row in EVAL_SCORING_ROWS)
    assert "classification task" not in text
    assert "summarization task" not in text


def test_run_button_initial_disabled_state_uses_nicegui_api() -> None:
    text = Path("src/openrouter_demo/ui.py").read_text()

    assert 'run_button.props("disable")' not in text
    assert "run_button.disable()" in text


def test_brand_label_is_grouped_with_avatar() -> None:
    text = Path("src/openrouter_demo/ui.py").read_text()

    assert ".demo-brand-lockup" in text
    assert 'with ui.column().classes("demo-brand-lockup"):' in text
    assert 'ui.image("/assets/ish-avatar.png").classes("demo-avatar")' in text
    assert 'ui.label("ishlab").classes("demo-brand-label")' in text


def test_prompt_panel_does_not_expose_simulated_failure_option() -> None:
    text = Path("src/openrouter_demo/ui.py").read_text()

    assert "Simulate primary route failure" not in text
    assert "simulate_failure" not in text
