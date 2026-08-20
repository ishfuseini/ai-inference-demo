from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from nicegui import ui

from openrouter_demo.client import OpenRouterError, stream_chat_completion
from openrouter_demo.config import LANGFUSE_ENV_VARS, OPENROUTER_API_KEY, AppConfig
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
    Unavailable,
)
from openrouter_demo.routing import (
    DEFAULT_STRATEGY,
    ROUTING_STRATEGY_LABELS,
    STRATEGIES,
    RoutingStrategy,
)
from openrouter_demo.scenarios import FallbackResult, run_fallback_scenario
from openrouter_demo.telemetry import record_trace

type StreamFn = Callable[..., AsyncIterator[StreamChunk | StreamedResult]]


_UNAVAILABLE_COPY = "Unavailable from selected route/provider."
_COST_UNAVAILABLE_COPY = "Cost metadata was not returned for this route/provider."
_LATENCY_UNAVAILABLE_COPY = "Latency was not returned for this route/provider."


def _format_metadata(value: str | Unavailable) -> str:
    if isinstance(value, Unavailable):
        return _UNAVAILABLE_COPY
    return value


def _format_tokens(value: int | Unavailable) -> str:
    if isinstance(value, Unavailable):
        return _UNAVAILABLE_COPY
    return str(value)


def _format_latency(value: int | Unavailable) -> str:
    if isinstance(value, Unavailable):
        return _LATENCY_UNAVAILABLE_COPY
    return f"{value} ms"


def _format_cost(value: float | Unavailable) -> str:
    if isinstance(value, Unavailable):
        return _COST_UNAVAILABLE_COPY
    return f"${value:g}"


def _format_cache_cell(telemetry: TelemetryEvidence | None) -> str:
    if telemetry is None:
        return _UNAVAILABLE_COPY
    if telemetry.cache_status == "hit":
        return f"Cache hit ({_format_tokens(telemetry.cached_tokens)} tokens)"
    if telemetry.cache_status == "write":
        return f"Cache write ({_format_tokens(telemetry.cache_write_tokens)} tokens)"
    return _UNAVAILABLE_COPY


def _format_trace_cell(telemetry: TelemetryEvidence | None) -> str:
    if telemetry is None:
        return _UNAVAILABLE_COPY
    if telemetry.trace_status == "enabled":
        return telemetry.trace_url or telemetry.trace_id or _UNAVAILABLE_COPY
    if telemetry.trace_status == "disabled":
        return TRACE_DISABLED
    return _UNAVAILABLE_COPY


def _format_router_cell(telemetry: TelemetryEvidence | None) -> str:
    if telemetry is None:
        return _UNAVAILABLE_COPY
    meta = telemetry.openrouter_metadata
    if isinstance(meta, dict):
        router_id = meta.get("id") or meta.get("upstream_id")
        if isinstance(router_id, str) and router_id:
            return router_id
    return _UNAVAILABLE_COPY


SAMPLE_PROMPTS = (
    "Explain eventual consistency to a backend engineer.",
    "Summarize this incident report for a customer.",
    "Classify this support ticket by severity.",
    "Extract action items from this meeting note.",
)

EMPTY_RESPONSE = "Run an inference request to see streaming output."
STREAMING_RESPONSE = "Streaming from OpenRouter..."
SUCCESS_RESPONSE = "Request completed successfully."
FAILURE_RESPONSE = "Request failed before fallback could complete."
FALLBACK_SUCCESS_RESPONSE = "Completed via fallback route after primary route failed."
SIMULATED_FAILURE_LABEL = "Simulated failure triggered for demo."
TRACE_DISABLED = "Langfuse tracing disabled. Configure Langfuse credentials to enable trace links."


@dataclass
class _UIState:
    is_running: bool = False
    last_run: InferenceRun | None = None
    response: str = ""
    response_status: str = EMPTY_RESPONSE


def _telemetry_rows(run: InferenceRun | None, *, is_running: bool = False) -> list[tuple[str, str]]:
    strategy = (
        (run.strategy_name or DEFAULT_STRATEGY.name) if run is not None else DEFAULT_STRATEGY.name
    )
    if is_running:
        return [
            ("Status", STREAMING_RESPONSE),
            ("Strategy", strategy),
            ("Model", _format_metadata(Unavailable())),
            ("Provider", _format_metadata(Unavailable())),
            ("Latency", _format_latency(Unavailable())),
            ("Tokens", _format_tokens(Unavailable())),
            ("Cost", _format_cost(Unavailable())),
            ("Router", _format_router_cell(None)),
            ("Cache", _format_cache_cell(None)),
            ("Trace", _format_trace_cell(None)),
        ]
    if run is None:
        return [
            ("Status", "Waiting for request."),
            ("Strategy", strategy),
            ("Model", _format_metadata(Unavailable())),
            ("Provider", _format_metadata(Unavailable())),
            ("Latency", _format_latency(Unavailable())),
            ("Tokens", _format_tokens(Unavailable())),
            ("Cost", _format_cost(Unavailable())),
            ("Router", _format_router_cell(None)),
            ("Cache", _format_cache_cell(None)),
            ("Trace", _format_trace_cell(None)),
        ]

    telemetry = run.telemetry
    if run.status is Status.FALLBACK_SUCCEEDED:
        status = FALLBACK_SUCCESS_RESPONSE
    elif run.status is Status.SUCCEEDED:
        status = SUCCESS_RESPONSE
    else:
        status = FAILURE_RESPONSE
    rows = [
        ("Status", status),
        ("Strategy", strategy),
        (
            "Model",
            _format_metadata(telemetry.model) if telemetry else _format_metadata(Unavailable()),
        ),
        (
            "Provider",
            _format_metadata(telemetry.provider) if telemetry else _format_metadata(Unavailable()),
        ),
        (
            "Latency",
            _format_latency(telemetry.latency_ms) if telemetry else _format_latency(Unavailable()),
        ),
        (
            "Tokens",
            _format_tokens(telemetry.total_tokens) if telemetry else _format_tokens(Unavailable()),
        ),
        ("Cost", _format_cost(telemetry.cost_usd) if telemetry else _format_cost(Unavailable())),
        ("Router", _format_router_cell(telemetry)),
        ("Cache", _format_cache_cell(telemetry)),
        ("Trace", _format_trace_cell(telemetry)),
    ]
    if run.fallback_evidence is not None:
        fe = run.fallback_evidence
        rows.append(("Primary status", fe.primary.status.value))
        rows.append(("Primary error", fe.primary.error_message or _UNAVAILABLE_COPY))
        rows.append(("Fallback model", _format_metadata(fe.fallback.model)))
        rows.append(("Fallback status", fe.fallback.status.value))
        if fe.simulated:
            rows.append(("Failure type", SIMULATED_FAILURE_LABEL))
    return rows


def _history_rows(
    history: RunHistory,
) -> list[tuple[str, str, str, str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str, str, str, str]] = []
    for index, run in enumerate(history.all(), start=1):
        telemetry = run.telemetry
        fallback_label = "Yes" if run.fallback_evidence is not None else "—"
        rows.append(
            (
                str(index),
                run.strategy_name,
                _format_metadata(telemetry.model) if telemetry else _format_metadata(Unavailable()),
                _format_metadata(telemetry.provider)
                if telemetry
                else _format_metadata(Unavailable()),
                _format_latency(telemetry.latency_ms)
                if telemetry
                else _format_latency(Unavailable()),
                _format_tokens(telemetry.total_tokens)
                if telemetry
                else _format_tokens(Unavailable()),
                _format_cost(telemetry.cost_usd) if telemetry else _format_cost(Unavailable()),
                fallback_label,
            )
        )
    return rows


def _render_telemetry(run: InferenceRun | None, *, is_running: bool = False) -> None:
    with ui.card().classes("w-full"):
        ui.label("Telemetry").classes("font-semibold")
        for label, value in _telemetry_rows(run, is_running=is_running):
            with ui.row().classes("w-full justify-between gap-4"):
                ui.label(label).classes("text-sm text-gray-600")
                ui.label(value).classes("text-sm font-medium")


def _render_history(history: RunHistory) -> None:
    with ui.card().classes("w-full"):
        ui.label("Run history").classes("font-semibold")
        rows = _history_rows(history)
        if not rows:
            ui.label(
                "Previous runs will appear here for cost, latency, and route comparison."
            ).classes("text-sm text-gray-600")
            return
        columns = ("Run", "Strategy", "Model", "Provider", "Latency", "Tokens", "Cost", "Fallback")
        with ui.grid(columns=len(columns)).classes("w-full gap-2 text-sm"):
            for column in columns:
                ui.label(column).classes("font-semibold")
            for row in rows:
                for value in row:
                    ui.label(value)


async def _run_inference(
    prompt: str,
    *,
    api_key: str,
    history: RunHistory,
    stream_fn: StreamFn = stream_chat_completion,
    strategy: RoutingStrategy = DEFAULT_STRATEGY,
    config: AppConfig | None = None,
) -> InferenceRun:
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("Prompt must not be blank.")

    started_at = datetime.now(UTC)
    text_parts: list[str] = []

    try:
        async for event in stream_fn(prompt, strategy=strategy, api_key=api_key):
            if isinstance(event, StreamChunk):
                text_parts.append(event.text_delta)
                continue

            trace_status: str | Unavailable = UNAVAILABLE
            trace_id: str | None = None
            trace_url: str | None = None
            if config is not None:
                model_for_trace = (
                    event.model if not isinstance(event.model, Unavailable) else strategy.model
                )
                usage_details: dict[str, int] = {}
                if not isinstance(event.prompt_tokens, Unavailable):
                    usage_details["prompt_tokens"] = event.prompt_tokens
                if not isinstance(event.completion_tokens, Unavailable):
                    usage_details["completion_tokens"] = event.completion_tokens
                outcome = record_trace(
                    config=config,
                    name="openrouter-inference",
                    model=model_for_trace,
                    input={"prompt": prompt},
                    output=event.text,
                    usage_details=usage_details,
                )
                trace_status = outcome.status
                trace_id = outcome.trace_id
                trace_url = outcome.trace_url

            telemetry = TelemetryEvidence(
                model=event.model,
                provider=event.provider,
                latency_ms=event.latency_ms,
                prompt_tokens=event.prompt_tokens,
                completion_tokens=event.completion_tokens,
                total_tokens=event.total_tokens,
                cost_usd=event.cost_usd,
                cache_status=event.cache_status,
                cached_tokens=event.cached_tokens,
                cache_write_tokens=event.cache_write_tokens,
                openrouter_metadata=event.openrouter_metadata,
                trace_status=trace_status,
                trace_id=trace_id,
                trace_url=trace_url,
            )
            run = InferenceRun(
                run_id=uuid.uuid4().hex,
                prompt=prompt,
                strategy_name=strategy.name,
                started_at=started_at,
                completed_at=datetime.now(UTC),
                status=Status.SUCCEEDED,
                streamed_text=event.text or "".join(text_parts),
                error_message=None,
                telemetry=telemetry,
            )
            history.append(run)
            return run
    except OpenRouterError as exc:
        run = InferenceRun(
            run_id=uuid.uuid4().hex,
            prompt=prompt,
            strategy_name=strategy.name,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            status=Status.FAILED,
            streamed_text=exc.partial_text or "".join(text_parts),
            error_message=str(exc),
            telemetry=None,
        )
        history.append(run)
        return run

    run = InferenceRun(
        run_id=uuid.uuid4().hex,
        prompt=prompt,
        strategy_name=strategy.name,
        started_at=started_at,
        completed_at=datetime.now(UTC),
        status=Status.FAILED,
        streamed_text="".join(text_parts),
        error_message="OpenRouter stream ended without a final result.",
        telemetry=None,
    )
    history.append(run)
    return run


async def _run_fallback_inference(
    prompt: str,
    *,
    api_key: str,
    history: RunHistory,
    fallback_strategy: RoutingStrategy,
    stream_fn: StreamFn = stream_chat_completion,
    config: AppConfig | None = None,
) -> InferenceRun:
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("Prompt must not be blank.")

    started_at = datetime.now(UTC)
    text_parts: list[str] = []
    fallback_result: StreamedResult | None = None
    primary_record: AttemptRecord | None = None

    async for event in run_fallback_scenario(
        prompt,
        fallback_strategy=fallback_strategy,
        api_key=api_key,
        stream_fn=stream_fn,
    ):
        if isinstance(event, StreamChunk):
            text_parts.append(event.text_delta)
        elif isinstance(event, FallbackResult):
            primary_record = event.primary
            fallback_result = event.fallback

    if fallback_result is None or primary_record is None:
        # Edge case: primary unexpectedly succeeded — treat as normal run
        run = InferenceRun(
            run_id=uuid.uuid4().hex,
            prompt=prompt,
            strategy_name=fallback_strategy.name,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            status=Status.SUCCEEDED,
            streamed_text="".join(text_parts),
            error_message=None,
            telemetry=None,
        )
        history.append(run)
        return run

    trace_status: str | Unavailable = UNAVAILABLE
    trace_id: str | None = None
    trace_url: str | None = None
    if config is not None:
        model_for_trace = (
            fallback_result.model
            if not isinstance(fallback_result.model, Unavailable)
            else fallback_strategy.model
        )
        usage_details: dict[str, int] = {}
        if not isinstance(fallback_result.prompt_tokens, Unavailable):
            usage_details["prompt_tokens"] = fallback_result.prompt_tokens
        if not isinstance(fallback_result.completion_tokens, Unavailable):
            usage_details["completion_tokens"] = fallback_result.completion_tokens
        outcome = record_trace(
            config=config,
            name="openrouter-inference",
            model=model_for_trace,
            input={"prompt": prompt},
            output=fallback_result.text,
            usage_details=usage_details,
        )
        trace_status = outcome.status
        trace_id = outcome.trace_id
        trace_url = outcome.trace_url

    telemetry = TelemetryEvidence(
        model=fallback_result.model,
        provider=fallback_result.provider,
        latency_ms=fallback_result.latency_ms,
        prompt_tokens=fallback_result.prompt_tokens,
        completion_tokens=fallback_result.completion_tokens,
        total_tokens=fallback_result.total_tokens,
        cost_usd=fallback_result.cost_usd,
        cache_status=fallback_result.cache_status,
        cached_tokens=fallback_result.cached_tokens,
        cache_write_tokens=fallback_result.cache_write_tokens,
        openrouter_metadata=fallback_result.openrouter_metadata,
        trace_status=trace_status,
        trace_id=trace_id,
        trace_url=trace_url,
    )
    fallback_attempt_record = AttemptRecord(
        model=fallback_result.model,
        provider=fallback_result.provider,
        status=Status.SUCCEEDED,
        error_message=None,
        latency_ms=fallback_result.latency_ms,
        prompt_tokens=fallback_result.prompt_tokens,
        completion_tokens=fallback_result.completion_tokens,
        total_tokens=fallback_result.total_tokens,
        cost_usd=fallback_result.cost_usd,
    )
    evidence = FallbackEvidence(
        primary=primary_record,
        fallback=fallback_attempt_record,
        simulated=True,
    )
    run = InferenceRun(
        run_id=uuid.uuid4().hex,
        prompt=prompt,
        strategy_name=fallback_strategy.name,
        started_at=started_at,
        completed_at=datetime.now(UTC),
        status=Status.FALLBACK_SUCCEEDED,
        streamed_text=fallback_result.text or "".join(text_parts),
        error_message=None,
        telemetry=telemetry,
        fallback_evidence=evidence,
    )
    history.append(run)
    return run


def _status(label: str, ready: bool, detail: str) -> None:
    color = "positive" if ready else "warning"
    with ui.card().classes("w-full"):
        ui.label(label).classes("text-lg font-semibold")
        ui.badge("Ready" if ready else "Needs setup", color=color)
        ui.label(detail).classes("text-sm text-gray-600")


def build_app(
    config: AppConfig,
    history: RunHistory,
    *,
    stream_fn: StreamFn = stream_chat_completion,
) -> None:
    ui.page_title("OpenRouter Production Inference Lab")
    state = _UIState()

    def sync_run_button() -> None:
        disabled = (
            not config.openrouter_ready or state.is_running or not str(prompt.value or "").strip()
        )
        if disabled:
            run_button.disable()
        else:
            run_button.enable()

    @ui.refreshable
    def response_panel() -> None:
        with ui.card().classes("w-full"):
            ui.label("Streaming response").classes("font-semibold")
            ui.label(state.response_status).classes("text-sm text-gray-600")
            ui.label(state.response or EMPTY_RESPONSE).classes("whitespace-pre-wrap")

    @ui.refreshable
    def telemetry_panel() -> None:
        _render_telemetry(state.last_run, is_running=state.is_running)

    @ui.refreshable
    def history_panel() -> None:
        _render_history(history)

    def refresh(panel: object) -> None:
        cast(Any, panel).refresh()

    async def run_request() -> None:
        if not config.openrouter_ready or state.is_running:
            return
        prompt_text = str(prompt.value or "").strip()
        if not prompt_text:
            sync_run_button()
            return

        state.is_running = True
        state.response = ""
        state.response_status = STREAMING_RESPONSE
        sync_run_button()
        refresh(response_panel)
        refresh(telemetry_panel)

        async def observed_stream(
            prompt_value: str, **kwargs: object
        ) -> AsyncIterator[StreamChunk | StreamedResult]:
            async for event in stream_fn(prompt_value, **kwargs):
                if isinstance(event, StreamChunk):
                    state.response = state.response + event.text_delta
                    refresh(response_panel)
                yield event

        selected_strategy = STRATEGIES.get(strategy_select.value, DEFAULT_STRATEGY)
        if simulate_failure.value:
            run = await _run_fallback_inference(
                prompt_text,
                api_key=os.environ.get(OPENROUTER_API_KEY, ""),
                history=history,
                fallback_strategy=selected_strategy,
                stream_fn=observed_stream,
                config=config,
            )
        else:
            run = await _run_inference(
                prompt_text,
                api_key=os.environ.get(OPENROUTER_API_KEY, ""),
                history=history,
                stream_fn=observed_stream,
                strategy=selected_strategy,
                config=config,
            )
        state.is_running = False
        state.last_run = run
        state.response = run.streamed_text
        if run.status is Status.FALLBACK_SUCCEEDED:
            state.response_status = FALLBACK_SUCCESS_RESPONSE
        elif run.status is Status.SUCCEEDED:
            state.response_status = SUCCESS_RESPONSE
        else:
            state.response_status = FAILURE_RESPONSE
        sync_run_button()
        refresh(response_panel)
        refresh(telemetry_panel)
        refresh(history_panel)

    def fill_prompt(value: str) -> None:
        prompt.value = value
        sync_run_button()

    with ui.column().classes("mx-auto w-full max-w-5xl gap-4 p-6"):
        ui.label("OpenRouter Production Inference Lab").classes("text-3xl font-bold")
        ui.label("Route, observe, recover, and evaluate model calls.").classes("text-gray-600")
        ui.label("A model call is easy. Operating inference is the real problem.").classes(
            "text-sm text-gray-600"
        )

        with ui.row().classes("w-full gap-4"):
            _status(
                "OpenRouter",
                config.openrouter_ready,
                "Export OPENROUTER_API_KEY before live inference."
                if not config.openrouter_ready
                else "Required credential is present; value is not displayed.",
            )
            _status(
                "Langfuse tracing",
                config.langfuse_ready,
                TRACE_DISABLED
                if not config.langfuse_ready
                else "Optional tracing credentials are present; values are not displayed.",
            )

        if not config.openrouter_ready:
            with ui.card().classes("w-full bg-amber-50"):
                ui.label("Setup needed").classes("font-semibold")
                ui.label(f"Set {OPENROUTER_API_KEY} in your shell, then restart the app.")

        with ui.card().classes("w-full"):
            ui.label("Prompt").classes("font-semibold")
            prompt = ui.textarea(
                placeholder="Ask a production-style question, classification task, or summarization task...",
                on_change=lambda _: sync_run_button(),
            ).classes("w-full")
            ui.label("Sample prompt").classes("text-sm font-semibold")
            with ui.row().classes("w-full gap-2"):
                for sample in SAMPLE_PROMPTS:
                    ui.button(sample, on_click=lambda sample=sample: fill_prompt(sample)).props(
                        "flat dense"
                    )
            ui.label("Strategy").classes("font-semibold")
            strategy_select = ui.select(
                options={s.name: ROUTING_STRATEGY_LABELS[s.name] for s in STRATEGIES.values()},
                value=DEFAULT_STRATEGY.name,
            ).classes("w-full")
            strategy_description_label = ui.label(DEFAULT_STRATEGY.description).classes(
                "text-sm text-gray-600"
            )

            def update_strategy_description(_: object) -> None:
                selected = STRATEGIES.get(strategy_select.value, DEFAULT_STRATEGY)
                strategy_description_label.text = selected.description

            strategy_select.on("update:model-value", update_strategy_description)
            simulate_failure = ui.switch("Simulate primary route failure", value=False)
            ui.label("For a reproducible demo. The UI will label this as simulated.").classes(
                "text-sm text-gray-600"
            )
            run_button = ui.button("Run Inference", on_click=run_request)
            run_button.props("disable")

        with ui.row().classes("w-full gap-4"):
            response_panel()
            telemetry_panel()

        history_panel()

        with ui.card().classes("w-full"):
            ui.label("Future operation panels").classes("font-semibold")
            ui.label(
                "Cache, trace links, and eval execution stay reserved for later phases."
            ).classes("text-sm text-gray-600")
            ui.label("Optional Langfuse variables: " + ", ".join(LANGFUSE_ENV_VARS)).classes(
                "text-sm text-gray-600"
            )
