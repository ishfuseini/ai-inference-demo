from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from typing import Any, cast

from nicegui import ui

from openrouter_demo.client import OpenRouterError, stream_chat_completion
from openrouter_demo.config import LANGFUSE_ENV_VARS, OPENROUTER_API_KEY, AppConfig
from openrouter_demo.history import RunHistory
from openrouter_demo.models import (
    InferenceRun,
    Status,
    StreamChunk,
    StreamedResult,
    TelemetryEvidence,
    Unavailable,
)
from openrouter_demo.routing import DEFAULT_STRATEGY, RoutingStrategy

type StreamFn = Callable[..., AsyncIterator[StreamChunk | StreamedResult]]


def _format_metadata(value: str | Unavailable) -> str:
    if isinstance(value, Unavailable):
        return "Unavailable from selected route/provider."
    return value


def _format_tokens(value: int | Unavailable) -> str:
    if isinstance(value, Unavailable):
        return "Unavailable from selected route/provider."
    return str(value)


def _format_cost(value: float | Unavailable) -> str:
    if isinstance(value, Unavailable):
        return "Cost metadata was not returned for this route/provider."
    return f"${value:g}"

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
TRACE_DISABLED = "Langfuse tracing disabled. Configure Langfuse credentials to enable trace links."


def _telemetry_rows(run: InferenceRun | None, *, is_running: bool = False) -> list[tuple[str, str]]:
    if is_running:
        return [
            ("Status", STREAMING_RESPONSE),
            ("Strategy", "Default"),
            ("Model", _format_metadata(Unavailable())),
            ("Provider", _format_metadata(Unavailable())),
            ("Latency", _format_tokens(Unavailable())),
            ("Tokens", _format_tokens(Unavailable())),
            ("Cost", _format_cost(Unavailable())),
        ]
    if run is None:
        return [
            ("Status", "Waiting for request."),
            ("Strategy", "Default"),
            ("Model", _format_metadata(Unavailable())),
            ("Provider", _format_metadata(Unavailable())),
            ("Latency", _format_tokens(Unavailable())),
            ("Tokens", _format_tokens(Unavailable())),
            ("Cost", _format_cost(Unavailable())),
        ]

    telemetry = run.telemetry
    status = SUCCESS_RESPONSE if run.status is Status.SUCCEEDED else FAILURE_RESPONSE
    return [
        ("Status", status),
        ("Strategy", "Default"),
        ("Model", _format_metadata(telemetry.model) if telemetry else _format_metadata(Unavailable())),
        ("Provider", _format_metadata(telemetry.provider) if telemetry else _format_metadata(Unavailable())),
        (
            "Latency",
            f"{telemetry.latency_ms} ms" if telemetry else _format_tokens(Unavailable()),
        ),
        (
            "Tokens",
            _format_tokens(telemetry.total_tokens) if telemetry else _format_tokens(Unavailable()),
        ),
        ("Cost", _format_cost(telemetry.cost_usd) if telemetry else _format_cost(Unavailable())),
    ]


def _history_rows(history: RunHistory) -> list[tuple[str, str, str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str, str, str]] = []
    for index, run in enumerate(history.all(), start=1):
        telemetry = run.telemetry
        rows.append(
            (
                str(index),
                run.strategy_name,
                _format_metadata(telemetry.model) if telemetry else _format_metadata(Unavailable()),
                _format_metadata(telemetry.provider) if telemetry else _format_metadata(Unavailable()),
                f"{telemetry.latency_ms} ms" if telemetry else _format_tokens(Unavailable()),
                _format_tokens(telemetry.total_tokens) if telemetry else _format_tokens(Unavailable()),
                _format_cost(telemetry.cost_usd) if telemetry else _format_cost(Unavailable()),
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
            ui.label("Previous runs will appear here for cost, latency, and route comparison.").classes(
                "text-sm text-gray-600"
            )
            return
        columns = ("Run", "Strategy", "Model", "Provider", "Latency", "Tokens", "Cost")
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

            telemetry = TelemetryEvidence(
                model=event.model,
                provider=event.provider,
                latency_ms=event.latency_ms,
                prompt_tokens=event.prompt_tokens,
                completion_tokens=event.completion_tokens,
                total_tokens=event.total_tokens,
                cost_usd=event.cost_usd,
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
    state: dict[str, InferenceRun | bool | str | None] = {
        "is_running": False,
        "last_run": None,
        "response": "",
        "response_status": EMPTY_RESPONSE,
    }

    def sync_run_button() -> None:
        disabled = (
            not config.openrouter_ready
            or bool(state["is_running"])
            or not str(prompt.value or "").strip()
        )
        if disabled:
            run_button.disable()
        else:
            run_button.enable()

    @ui.refreshable
    def response_panel() -> None:
        with ui.card().classes("w-full"):
            ui.label("Streaming response").classes("font-semibold")
            ui.label(str(state["response_status"])).classes("text-sm text-gray-600")
            ui.label(str(state["response"] or EMPTY_RESPONSE)).classes("whitespace-pre-wrap")

    @ui.refreshable
    def telemetry_panel() -> None:
        _render_telemetry(
            state["last_run"] if isinstance(state["last_run"], InferenceRun) else None,
            is_running=bool(state["is_running"]),
        )

    @ui.refreshable
    def history_panel() -> None:
        _render_history(history)

    def refresh(panel: object) -> None:
        cast(Any, panel).refresh()

    async def run_request() -> None:
        if not config.openrouter_ready or bool(state["is_running"]):
            return
        prompt_text = str(prompt.value or "").strip()
        if not prompt_text:
            sync_run_button()
            return

        state["is_running"] = True
        state["response"] = ""
        state["response_status"] = STREAMING_RESPONSE
        sync_run_button()
        refresh(response_panel)
        refresh(telemetry_panel)

        async def observed_stream(
            prompt_value: str, **kwargs: object
        ) -> AsyncIterator[StreamChunk | StreamedResult]:
            async for event in stream_fn(prompt_value, **kwargs):
                if isinstance(event, StreamChunk):
                    state["response"] = str(state["response"]) + event.text_delta
                    refresh(response_panel)
                yield event

        run = await _run_inference(
            prompt_text,
            api_key=os.environ.get(OPENROUTER_API_KEY, ""),
            history=history,
            stream_fn=observed_stream,
            strategy=DEFAULT_STRATEGY,
        )
        state["is_running"] = False
        state["last_run"] = run
        state["response"] = run.streamed_text
        state["response_status"] = (
            SUCCESS_RESPONSE if run.status is Status.SUCCEEDED else FAILURE_RESPONSE
        )
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
            ui.label("Default").classes("font-semibold")
            ui.label(DEFAULT_STRATEGY.description).classes("text-sm text-gray-600")
            run_button = ui.button("Run Inference", on_click=run_request)
            run_button.props("disable")

        with ui.row().classes("w-full gap-4"):
            response_panel()
            telemetry_panel()

        history_panel()

        with ui.card().classes("w-full"):
            ui.label("Future operation panels").classes("font-semibold")
            ui.label(
                "Fallback, cache, trace links, and eval execution stay reserved for later phases."
            ).classes("text-sm text-gray-600")
            ui.label("Optional Langfuse variables: " + ", ".join(LANGFUSE_ENV_VARS)).classes(
                "text-sm text-gray-600"
            )
