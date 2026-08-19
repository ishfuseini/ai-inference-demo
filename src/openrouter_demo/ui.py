from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime

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


def build_app(config: AppConfig) -> None:
    ui.page_title("OpenRouter Production Inference Lab")
    with ui.column().classes("mx-auto w-full max-w-5xl gap-4 p-6"):
        ui.label("OpenRouter Production Inference Lab").classes("text-3xl font-bold")
        ui.label("Route, observe, recover, and evaluate model calls.").classes("text-gray-600")

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
                "Optional tracing disabled until all Langfuse env vars are exported."
                if not config.langfuse_ready
                else "Optional tracing credentials are present; values are not displayed.",
            )

        if not config.openrouter_ready:
            with ui.card().classes("w-full bg-amber-50"):
                ui.label("Setup needed").classes("font-semibold")
                ui.label(f"Set {OPENROUTER_API_KEY} in your shell, then restart the app.")

        with ui.card().classes("w-full"):
            ui.label("Prompt").classes("font-semibold")
            ui.textarea(placeholder="Ask a small production-inference question...").classes("w-full")
            ui.button("Sample prompt", on_click=lambda: None)
            ui.button("Run Inference").props("disable")
            ui.label("Live inference starts in Phase 2; no request is sent in Phase 1.").classes(
                "text-sm text-gray-600"
            )

        with ui.card().classes("w-full"):
            ui.label("Future operation panels").classes("font-semibold")
            ui.label("Routing, fallback, telemetry, cache observations, and evals are intentionally empty in Phase 1.")
            ui.label("Optional Langfuse variables: " + ", ".join(LANGFUSE_ENV_VARS)).classes(
                "text-sm text-gray-600"
            )
