import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

from openrouter_demo.client import OpenRouterHTTPError
from openrouter_demo.config import load_config
from openrouter_demo.models import (
    UNAVAILABLE,
    Status,
    StreamChunk,
    StreamedResult,
)
from openrouter_demo.routing import (
    COST_STRATEGY,
    DEFAULT_STRATEGY,
    STRATEGIES,
)
from openrouter_demo.sqlite_store import SQLiteRunHistory
from openrouter_demo.ui import (
    EVAL_DESCRIPTION,
    SAMPLE_PROMPTS,
    STRATEGY_MODELS,
    _format_cost,
    _format_metadata,
    _run_inference,
    _strategy_with_model,
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


def test_strategies_dict_contains_two_selectable_strategies() -> None:
    assert set(STRATEGIES.keys()) == {"cost", "intelligence"}


def test_strategy_with_model_preserves_routing_preferences() -> None:
    strategy = _strategy_with_model(COST_STRATEGY, "mistralai/mistral-nemo")

    assert strategy.name == COST_STRATEGY.name
    assert strategy.description == COST_STRATEGY.description
    assert strategy.provider_preferences == COST_STRATEGY.provider_preferences
    assert strategy.model == "mistralai/mistral-nemo"
    assert COST_STRATEGY.model == DEFAULT_STRATEGY.model


def test_strategy_models_are_hard_coded_by_strategy() -> None:
    assert STRATEGY_MODELS == {
        "cost": "openai/gpt-oss-20b:free",
        "intelligence": "anthropic/claude-opus-5",
    }
    assert set(STRATEGY_MODELS) == set(STRATEGIES)


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


def test_ui_has_no_chatbot_labels() -> None:
    text = Path("src/openrouter_demo/ui.py").read_text()
    for inference_copy in (
        'ui.page_title("ishlab Production Inference Lab")',
        '_heading("Production Inference Lab", level=1, classes="demo-page-title")',
        "The app runs live streaming inference",
        "This demo shows what changes when inference becomes something you have to operate",
        'ui.button("Run Inference", on_click=run_request)',
        '"LLM Response"',
        '"Strategy"',
        'STRATEGY_MODEL_SHORT_NAMES[STRATEGY_MODELS[s.name]]',
        "demo-prompt-card",
        "rows=18",
        "demo-response-output",
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
    assert "ui.html(EVAL_DESCRIPTION)" in Path("src/openrouter_demo/ui.py").read_text()
    assert "API keeps failing" in EVAL_DESCRIPTION
    assert "Leads with the customer's problem" in EVAL_DESCRIPTION
    assert "Asks for real detail" in EVAL_DESCRIPTION
    assert "Commits to a next step" in EVAL_DESCRIPTION


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
