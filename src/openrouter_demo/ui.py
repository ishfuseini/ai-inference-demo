from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from nicegui import ui

from openrouter_demo.client import OpenRouterError, stream_chat_completion
from openrouter_demo.config import OPENROUTER_API_KEY, AppConfig
from openrouter_demo.history import RunHistory
from openrouter_demo.models import (
    UNAVAILABLE,
    AttemptRecord,
    FallbackEvidence,
    InferenceRun,
    RepeatObservation,
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
from openrouter_demo.scenarios import FallbackResult, run_fallback_scenario, run_repeat_scenario
from openrouter_demo.telemetry import record_trace

type StreamFn = Callable[..., AsyncIterator[StreamChunk | StreamedResult]]


_UNAVAILABLE_COPY = "Unavailable from selected route/provider."
_COST_UNAVAILABLE_COPY = "Cost metadata was not returned for this route/provider."
_LATENCY_UNAVAILABLE_COPY = "Latency was not returned for this route/provider."


# --- Design system (docs/design/DESIGN.md) ---

_DESIGN_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
  /* Core palette */
  --color-hero: #1f96db;
  --color-accent: #ed7c3a;
  --color-accent-secondary: #ab80f3;
  --color-neutral-light: #dedbf1;
  --color-neutral-lightest: #FCFDFE;
  --color-neutral-dark: #525252;
  --color-neutral-darkest: #2a3139;

  /* Semantic mapping */
  --color-primary: var(--color-hero);
  --color-primary-hover: #1a82be;
  --color-primary-subtle: #e8f4fb;
  --color-text-main: var(--color-neutral-darkest);
  --color-text-secondary: var(--color-neutral-dark);
  --color-surface: var(--color-neutral-lightest);
  --color-surface-alt: var(--color-neutral-light);
  --color-background: var(--color-neutral-light);
  --color-text-on-primary: #FFFFFF;
  --color-border: var(--color-neutral-light);
  --color-success: #15803D;
  --color-success-bg: #E8F5E9;
  --color-warning: var(--color-accent);
  --color-warning-bg: #FDF0E6;
  --color-error: #B91C1C;
  --color-error-bg: #FEE2E2;

  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-12: 3rem;
  --space-16: 4rem;

  /* Geometry — sharp corners */
  --radius: 0px;

  /* Typography */
  --font-ui: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;

  /* Quasar override */
  --q-primary: var(--color-hero);
}

body {
  font-family: var(--font-ui);
  color: var(--color-text-main);
  background-color: var(--color-background);
  --q-primary: var(--color-hero) !important;
  --q-positive: #15803D !important;
  --q-negative: #B91C1C !important;
  --q-warning: var(--color-accent) !important;
}

/* --- Typography --- */

.demo-page-title {
  font-family: var(--font-ui);
  font-weight: 700;
  font-size: 1.875rem;
  letter-spacing: -0.03em;
  color: var(--color-text-main);
}

.demo-subtitle {
  font-weight: 400;
  font-size: 1rem;
  color: var(--color-text-secondary);
}

.demo-supporting {
  font-weight: 400;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.demo-section-heading {
  font-weight: 700;
  font-size: 1.125rem;
  color: var(--color-text-main);
}

.demo-component-heading {
  font-weight: 600;
  font-size: 0.9375rem;
  color: var(--color-text-main);
}

.demo-label {
  font-weight: 500;
  font-size: 0.875rem;
  color: var(--color-text-main);
}

.demo-body {
  font-weight: 400;
  font-size: 0.875rem;
  color: var(--color-text-main);
}

.demo-secondary {
  font-weight: 400;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

/* --- Cards — sharp, flat, bordered --- */

.q-card.demo-card {
  background-color: var(--color-surface) !important;
  border-radius: var(--radius) !important;
  border: 1px solid var(--color-border) !important;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06) !important;
}

/* Setup banner */
.q-card.demo-setup-banner {
  background-color: var(--color-warning-bg) !important;
  border-radius: var(--radius) !important;
  border: 1px solid var(--color-warning) !important;
  border-left: 3px solid var(--color-warning) !important;
  box-shadow: none !important;
}

/* --- Buttons — accent orange, sharp corners --- */

.q-btn.demo-btn-primary,
.q-btn.demo-btn-primary.bg-primary,
.bg-primary.demo-btn-primary {
  background: var(--color-accent) !important;
  color: #FFFFFF !important;
  font-family: var(--font-ui);
  font-weight: 600;
  font-size: 0.9375rem;
  border-radius: var(--radius) !important;
  padding: var(--space-2) var(--space-6);
  transition: background-color 0.15s ease-out;
  box-shadow: none !important;
  text-transform: none !important;
}
.q-btn.demo-btn-primary:hover:not(.disabled) {
  background-color: #d46a2e !important;
}
.q-btn.demo-btn-primary.disabled {
  background-color: var(--color-border) !important;
  color: var(--color-text-secondary) !important;
  opacity: 1 !important;
}

/* Secondary button — ghost with border */
.q-btn.demo-btn-secondary {
  font-family: var(--font-ui);
  font-weight: 500;
  font-size: 0.8125rem;
  color: var(--color-hero) !important;
  background-color: transparent !important;
  border: 1px solid var(--color-border) !important;
  border-radius: var(--radius) !important;
  text-transform: none !important;
}
.q-btn.demo-btn-secondary:hover {
  border-color: var(--color-hero) !important;
}

/* --- Telemetry table — full width, bordered, no stripe --- */

.demo-telemetry-table {
  display: flex;
  flex-direction: column;
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  overflow: hidden;
}

.demo-telemetry-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  background-color: var(--color-surface);
}
.demo-telemetry-row:last-child {
  border-bottom: none;
}

.demo-telemetry-label {
  font-weight: 500;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.demo-telemetry-value {
  font-family: var(--font-mono);
  font-weight: 400;
  font-size: 0.8125rem;
  color: var(--color-text-main);
  text-align: right;
  max-width: 65%;
  word-break: break-word;
}

/* --- History grid --- */

.demo-grid-scroll {
  overflow-x: auto;
  width: 100%;
}

.demo-grid-scroll .nicegui-grid {
  min-width: max-content;
}

.demo-grid-header {
  font-weight: 600;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: var(--space-2) var(--space-3);
  border-bottom: 2px solid var(--color-border);
  white-space: nowrap;
}

.demo-grid-cell {
  font-family: var(--font-mono);
  font-weight: 400;
  font-size: 0.75rem;
  color: var(--color-text-main);
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}

/* --- Toggle / strategy --- */

.demo-toggle-help {
  font-weight: 400;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

.demo-strategy-desc {
  font-weight: 400;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  font-style: italic;
}

/* --- Response panel --- */

.demo-response-text {
  font-weight: 400;
  font-size: 0.9375rem;
  color: var(--color-text-main);
  line-height: 1.6;
  white-space: pre-wrap;
}

.demo-response-status {
  font-weight: 500;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.demo-response-status--success { color: var(--color-success); }
.demo-response-status--error { color: var(--color-error); }
.demo-response-status--streaming { color: var(--color-hero); }
.demo-response-status--fallback { color: var(--color-warning); }

/* --- Status bar --- */

.demo-status-bar {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  padding: var(--space-2) var(--space-4);
  background-color: var(--color-surface);
  border-radius: var(--radius);
  border: 1px solid var(--color-border);
}

.demo-status-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.demo-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.demo-status-dot--ready { background-color: var(--color-success); }
.demo-status-dot--warning { background-color: var(--color-warning); }

.demo-status-item-label {
  font-weight: 500;
  font-size: 0.8125rem;
  color: var(--color-text-main);
}

.demo-status-item-detail {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

/* --- Section divider --- */

.demo-section-divider {
  height: 1px;
  background-color: var(--color-border);
  margin: var(--space-3) 0;
}

/* --- Tabs --- */

.demo-tabs .q-tab {
  font-family: var(--font-ui);
  font-weight: 500;
  font-size: 0.875rem;
  text-transform: none;
  color: var(--color-text-secondary);
  padding: var(--space-2) var(--space-4);
  min-height: 40px;
}

.demo-tabs .q-tab--active {
  color: var(--color-hero);
}

.demo-tabs .q-tab__indicator {
  background-color: var(--color-accent);
  height: 2px;
}

.demo-tabs .q-tabs__bar {
  border-bottom: 1px solid var(--color-border);
  justify-content: flex-start;
}

/* Tab panels — transparent, no padding */
.q-tab-panels {
  background-color: transparent !important;
}

.q-tab-panel {
  padding: 0 !important;
}

/* --- Browser surfaces --- */

*:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

::selection {
  background-color: var(--color-primary-subtle);
  color: var(--color-text-main);
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: var(--color-surface);
}
::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 0;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-secondary);
}

@media (prefers-reduced-motion: reduce) {
  * {
    transition: none !important;
    animation: none !important;
  }
}
</style>
"""


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


def _format_cache_cell(run: InferenceRun | None) -> str:
    if run is None:
        return _UNAVAILABLE_COPY
    telemetry = run.telemetry
    if telemetry is None:
        return _UNAVAILABLE_COPY
    if telemetry.cache_status == "hit":
        return f"Cache hit ({_format_tokens(telemetry.cached_tokens)} tokens)"
    if telemetry.cache_status == "write":
        return f"Cache write ({_format_tokens(telemetry.cache_write_tokens)} tokens)"
    repeat = run.repeat_observation
    if repeat is not None:
        return (
            f"Observed repeat: {_format_latency(repeat.first.latency_ms)} → "
            f"{_format_latency(repeat.second.latency_ms)}; "
            f"{_format_cost(repeat.first.cost_usd)} → {_format_cost(repeat.second.cost_usd)}"
        )
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
        ("Cache", _format_cache_cell(run)),
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


def _history_cache_label(run: InferenceRun) -> str:
    telemetry = run.telemetry
    if telemetry is None:
        return "—"
    if telemetry.cache_status == "hit":
        return f"hit ({_format_tokens(telemetry.cached_tokens)})"
    if telemetry.cache_status == "write":
        return f"write ({_format_tokens(telemetry.cache_write_tokens)})"
    if run.repeat_observation is not None:
        return "Observed repeat"
    return "—"


def _history_trace_label(run: InferenceRun) -> str:
    telemetry = run.telemetry
    if telemetry is None:
        return "—"
    if telemetry.trace_status == "enabled":
        return telemetry.trace_url or telemetry.trace_id or "—"
    if telemetry.trace_status == "disabled":
        return "disabled"
    if telemetry.trace_status == "failed":
        return "failed"
    return "—"


def _history_rows(
    history: RunHistory,
) -> list[tuple[str, str, str, str, str, str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str, str, str, str, str, str]] = []
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
                _history_cache_label(run),
                _history_trace_label(run),
            )
        )
    return rows


def _comparison_rows(
    history: RunHistory, limit: int = 10
) -> list[tuple[str, str, str, str, str, str]]:
    completed = [
        run
        for run in history.all()
        if run.status in (Status.SUCCEEDED, Status.FALLBACK_SUCCEEDED)
    ]
    rows: list[tuple[str, str, str, str, str, str]] = []
    for run in completed[:limit]:
        telemetry = run.telemetry
        rows.append(
            (
                _format_metadata(telemetry.model) if telemetry else _format_metadata(Unavailable()),
                _format_metadata(telemetry.provider)
                if telemetry
                else _format_metadata(Unavailable()),
                _format_latency(telemetry.latency_ms)
                if telemetry
                else _format_latency(Unavailable()),
                _format_cost(telemetry.cost_usd) if telemetry else _format_cost(Unavailable()),
                _history_cache_label(run),
                _history_trace_label(run),
            )
        )
    return rows


def _render_telemetry(run: InferenceRun | None, *, is_running: bool = False) -> None:
    with ui.card().classes("w-full demo-card"):
        ui.label("Telemetry").classes("demo-section-heading")
        with ui.element("div").classes("demo-telemetry-table"):
            for label, value in _telemetry_rows(run, is_running=is_running):
                with ui.element("div").classes("demo-telemetry-row"):
                    ui.label(label).classes("demo-telemetry-label")
                    ui.label(value).classes("demo-telemetry-value")


def _render_history(history: RunHistory) -> None:
    with ui.card().classes("w-full demo-card"):
        ui.label("Run history").classes("demo-section-heading")
        rows = _history_rows(history)
        if not rows:
            ui.label(
                "Previous runs will appear here for cost, latency, and route comparison."
            ).classes("demo-secondary")
            return
        columns = ("Run", "Strategy", "Model", "Provider", "Latency", "Tokens", "Cost", "Fallback", "Cache", "Trace")
        with ui.element("div").classes("demo-grid-scroll"), ui.grid(columns=len(columns)).classes("w-full"):
                for column in columns:
                    ui.label(column).classes("demo-grid-header")
                for row in rows:
                    for value in row:
                        ui.label(value).classes("demo-grid-cell")

        comparison = _comparison_rows(history)
        if comparison:
            ui.label("Comparison").classes("demo-component-heading")
            comparison_columns = ("Model", "Provider", "Latency", "Cost", "Cache", "Trace")
            with ui.element("div").classes("demo-grid-scroll"), ui.grid(columns=len(comparison_columns)).classes("w-full"):
                    for column in comparison_columns:
                        ui.label(column).classes("demo-grid-header")
                    for row in comparison:
                        for value in row:
                            ui.label(value).classes("demo-grid-cell")


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


async def _run_repeat_inference(
    prompt: str,
    *,
    api_key: str,
    history: RunHistory,
    strategy: RoutingStrategy,
    config: AppConfig,
    stream_fn: StreamFn = stream_chat_completion,
) -> InferenceRun:
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("Prompt must not be blank.")

    started_at = datetime.now(UTC)
    text_parts: list[str] = []
    repeat: RepeatObservation | None = None

    try:
        async for event in run_repeat_scenario(
            prompt,
            strategy=strategy,
            api_key=api_key,
            stream_fn=stream_fn,
        ):
            if isinstance(event, StreamChunk):
                text_parts.append(event.text_delta)
            elif isinstance(event, RepeatObservation):
                repeat = event
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

    if repeat is None:
        run = InferenceRun(
            run_id=uuid.uuid4().hex,
            prompt=prompt,
            strategy_name=strategy.name,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            status=Status.FAILED,
            streamed_text="".join(text_parts),
            error_message="Repeat scenario ended without a final observation.",
            telemetry=None,
        )
        history.append(run)
        return run

    second = repeat.second
    trace_status: str | Unavailable = UNAVAILABLE
    trace_id: str | None = None
    trace_url: str | None = None
    model_for_trace = second.model if not isinstance(second.model, Unavailable) else strategy.model
    usage_details: dict[str, int] = {}
    if not isinstance(second.prompt_tokens, Unavailable):
        usage_details["prompt_tokens"] = second.prompt_tokens
    if not isinstance(second.completion_tokens, Unavailable):
        usage_details["completion_tokens"] = second.completion_tokens
    outcome = record_trace(
        config=config,
        name="openrouter-inference",
        model=model_for_trace,
        input={"prompt": prompt},
        output=second.text,
        usage_details=usage_details,
    )
    trace_status = outcome.status
    trace_id = outcome.trace_id
    trace_url = outcome.trace_url

    telemetry = TelemetryEvidence(
        model=second.model,
        provider=second.provider,
        latency_ms=second.latency_ms,
        prompt_tokens=second.prompt_tokens,
        completion_tokens=second.completion_tokens,
        total_tokens=second.total_tokens,
        cost_usd=second.cost_usd,
        cache_status=repeat.cache_status,
        cached_tokens=repeat.cached_tokens,
        cache_write_tokens=repeat.cache_write_tokens,
        openrouter_metadata=second.openrouter_metadata,
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
        streamed_text=second.text or "".join(text_parts),
        error_message=None,
        telemetry=telemetry,
        repeat_observation=repeat,
    )
    history.append(run)
    return run


def _status_item(label: str, ready: bool, detail: str) -> None:
    dot_class = "demo-status-dot--ready" if ready else "demo-status-dot--warning"
    short_detail = "Ready" if ready else "Needs setup"
    with ui.element("div").classes("demo-status-item"):
        ui.element("div").classes(f"demo-status-dot {dot_class}")
        ui.label(label).classes("demo-status-item-label")
        ui.label(short_detail).classes("demo-status-item-detail")


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
        with ui.card().classes("w-full demo-card"):
            ui.label("Streaming response").classes("demo-section-heading")
            status_class = "demo-response-status"
            if state.is_running:
                status_class += " demo-response-status--streaming"
            elif state.last_run is not None:
                if state.last_run.status is Status.FALLBACK_SUCCEEDED:
                    status_class += " demo-response-status--fallback"
                elif state.last_run.status is Status.SUCCEEDED:
                    status_class += " demo-response-status--success"
                else:
                    status_class += " demo-response-status--error"
            ui.label(state.response_status).classes(status_class)
            ui.label(state.response or EMPTY_RESPONSE).classes("demo-response-text")

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
        if repeat_enabled.value:
            run = await _run_repeat_inference(
                prompt_text,
                api_key=os.environ.get(OPENROUTER_API_KEY, ""),
                history=history,
                strategy=selected_strategy,
                config=config,
                stream_fn=observed_stream,
            )
        elif simulate_failure.value:
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

    with ui.column().classes("mx-auto w-full max-w-[1280px] gap-6 p-6"):
        ui.add_head_html(_DESIGN_CSS)

        # Header
        ui.label("OpenRouter Production Inference Lab").classes("demo-page-title")
        ui.label("Route, observe, recover, and evaluate model calls.").classes("demo-subtitle")
        ui.label("A model call is easy. Operating inference is the real problem.").classes(
            "demo-supporting"
        )

        # Compact inline status bar
        with ui.element("div").classes("demo-status-bar"):
            _status_item(
                "OpenRouter",
                config.openrouter_ready,
                "Export OPENROUTER_API_KEY before live inference."
                if not config.openrouter_ready
                else "Required credential is present; value is not displayed.",
            )
            _status_item(
                "Langfuse tracing",
                config.langfuse_ready,
                TRACE_DISABLED
                if not config.langfuse_ready
                else "Optional tracing credentials are present; values are not displayed.",
            )

        # Setup guidance (only when not ready)
        if not config.openrouter_ready:
            with ui.card().classes("w-full demo-setup-banner"):
                ui.label("Setup needed").classes("demo-component-heading")
                ui.label(f"Set {OPENROUTER_API_KEY} in your shell, then restart the app.").classes(
                    "demo-body"
                )

        # Request panel with section dividers
        with ui.card().classes("w-full demo-card"):
            ui.label("Prompt").classes("demo-component-heading")
            prompt = ui.textarea(
                placeholder="Ask a production-style question, classification task, or summarization task...",
                on_change=lambda _: sync_run_button(),
            ).classes("w-full")
            ui.label("Sample prompt").classes("demo-label")
            with ui.row().classes("w-full gap-2 flex-wrap"):
                for sample in SAMPLE_PROMPTS:
                    ui.button(sample, on_click=lambda sample=sample: fill_prompt(sample)).props(
                        "flat dense"
                    ).classes("demo-btn-secondary")

            ui.element("div").classes("demo-section-divider")

            ui.label("Strategy").classes("demo-component-heading")
            strategy_select = ui.select(
                options={s.name: ROUTING_STRATEGY_LABELS[s.name] for s in STRATEGIES.values()},
                value=DEFAULT_STRATEGY.name,
            ).classes("w-full")
            strategy_description_label = ui.label(DEFAULT_STRATEGY.description).classes(
                "demo-strategy-desc"
            )

            def update_strategy_description(_: object) -> None:
                selected = STRATEGIES.get(strategy_select.value, DEFAULT_STRATEGY)
                strategy_description_label.text = selected.description

            strategy_select.on("update:model-value", update_strategy_description)

            ui.element("div").classes("demo-section-divider")

            with ui.row().classes("w-full gap-8 items-center"):
                with ui.column().classes("gap-1"):
                    repeat_enabled = ui.switch("Repeat previous prompt", value=False)
                    ui.label(
                        "Runs the same prompt twice and reports cache evidence or latency/cost delta."
                    ).classes("demo-toggle-help")
                with ui.column().classes("gap-1"):
                    simulate_failure = ui.switch("Simulate primary route failure", value=False)
                    ui.label("For a reproducible demo. The UI will label this as simulated.").classes(
                        "demo-toggle-help"
                    )
            run_button = ui.button("Run Inference", on_click=run_request).classes(
                "demo-btn-primary"
            ).props("unelevated").style("--q-primary: var(--color-accent);")
            run_button.props("disable")

        # Response panel (full width)
        response_panel()

        # Tabbed evidence: Telemetry + Run History
        with ui.tabs().classes("w-full demo-tabs") as tabs:
            ui.tab("Telemetry")
            ui.tab("Run History")
        with ui.tab_panels(tabs, value="Telemetry").classes("w-full"):
            with ui.tab_panel("Telemetry"):
                telemetry_panel()
            with ui.tab_panel("Run History"):
                history_panel()
