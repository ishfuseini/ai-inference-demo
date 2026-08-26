from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from nicegui import app as ng_app
from nicegui import ui
from starlette.staticfiles import StaticFiles

from openrouter_demo.client import OpenRouterError, stream_chat_completion
from openrouter_demo.config import OPENROUTER_API_KEY, AppConfig
from openrouter_demo.formatting import format_cost, format_trace
from openrouter_demo.models import (
    UNAVAILABLE,
    InferenceRun,
    LangfuseScore,
    Status,
    StreamChunk,
    StreamedResult,
    TelemetryEvidence,
    Unavailable,
)
from openrouter_demo.routing import (
    DEFAULT_STRATEGY,
    INTELLIGENCE_STRATEGY,
    ROUTING_STRATEGY_LABELS,
    STRATEGIES,
    RoutingStrategy,
)
from openrouter_demo.sqlite_store import SQLiteRunHistory
from openrouter_demo.telemetry import (
    ObservationDetails,
    fetch_langfuse_scores,
    fetch_observation_details,
    record_trace,
)

type StreamFn = Callable[..., AsyncIterator[StreamChunk | StreamedResult]]


_UNAVAILABLE_COPY = "Unavailable from selected route/provider."
_COST_UNAVAILABLE_COPY = "Cost metadata was not returned for this route/provider."
_LATENCY_UNAVAILABLE_COPY = "Latency was not returned for this route/provider."

STRATEGY_MODELS: dict[str, list[str]] = {
    "cost": [
        "deepseek/deepseek-v4-flash-0731",
        "inclusionai/ling-3.0-flash",
        "upstage/solar-pro4",
    ],
    "intelligence": [
        "anthropic/claude-opus-5",
        "z-ai/glm-5.2",
        "deepseek/deepseek-v4-pro",
    ],
}

STRATEGY_MODEL_SHORT_NAMES: dict[str, str] = {
    "deepseek/deepseek-v4-flash-0731": "deepseek-v4-flash",
    "anthropic/claude-opus-5": "claude-opus-5",
    "inclusionai/ling-3.0-flash": "ling-3.0-flash",
    "upstage/solar-pro4": "solar-pro4",
    "z-ai/glm-5.2": "glm-5.2",
    "deepseek/deepseek-v4-pro": "deepseek-v4-pro",
}


# --- Design system (docs/design/DESIGN.md — Swiss/Grid) ---

_DESIGN_CSS = """
<!--
DIRECTION CONTRACT (docs/design/DESIGN.md)
THESIS: An inference operating surface set in the Swiss/Grid tradition — structure is
the message. The category-default dashboard of tinted cards and pill buttons is refused;
everything sits on a visible black rule system over paper white.
OWN-WORLD: Near-black #111111 on off-white #F7F7F5, one violet accent #8A2BE2,
Helvetica Neue at every size, 4/8/16px radii, 1/2/4rem spacing steps, hairline
#D8D7D2 rules, uppercase tracked micro-labels, tabular data on white panels.
STORY: The interviewer reads the lab like a typeset instrument: route, observe,
recover, evaluate — every piece of evidence aligned to the same grid.
FIRST VIEWPORT: Black status bar over the page; page title 40px tight on the left;
a single violet Run Inference button anchors the prompt card; telemetry is a ruled
label/value table, data in tabular mono.
FORM: Swiss Modernism grid (1950s International Typographic Style) applied to an
Operate surface; pinned by docs/design/DESIGN.md, no concept round.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish
review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.
-->
<style>
:root {
  /* Core palette — Swiss/Grid */
  --color-ink: #111111;
  --color-ink-secondary: #555555;
  --color-paper: #F7F7F5;
  --color-accent: #C495F0;
  --color-accent-hover: #B690DB;
  --color-accent-subtle: #F1E9FB;
  --color-sample-button: #B3B3B3;
  --color-sample-button-text: #4B4B4B;
  --color-rule: #D8D7D2;
  --color-rule-strong: #111111;

  /* Semantic mapping */
  --color-primary: var(--color-accent);
  --color-primary-hover: var(--color-accent-hover);
  --color-primary-subtle: var(--color-accent-subtle);
  --color-text-main: var(--color-ink);
  --color-text-secondary: var(--color-ink-secondary);
  --color-surface: #FFFFFF;
  --color-surface-alt: var(--color-paper);
  --color-background: var(--color-paper);
  --color-text-on-primary: #FFFFFF;
  --color-success: #15803D;
  --color-success-bg: #EAF4EC;
  --color-warning: #B45309;
  --color-warning-bg: #FBF3E4;
  --color-error: #B91C1C;
  --color-error-bg: #FBEAEA;

  /* Spacing — DESIGN.md steps: sm 1rem, md 2rem, lg 4rem */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-12: 3rem;
  --space-16: 4rem;

  /* Geometry — DESIGN.md radii: sm 4, md 8, lg 16 */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 16px;
  --radius: var(--radius-md);

  /* Typography — Helvetica Neue, the brief's only face */
  --font-ui: 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif;
  --font-mono: 'SF Mono', ui-monospace, Menlo, Consolas, monospace;

  /* Type ramp — one size per role.
     Roles below body are separated by whole steps, not 1px. */
  --text-page-title: 2.5rem;   /* 40px: page title (DESIGN.md h1) */
  --text-section: 1.25rem;     /* 20px: section headings */
  --text-body: 1rem;           /* 16px: body copy, prose, component headings, primary buttons */
  --text-label: 0.875rem;      /* 14px: labels, tabs, secondary buttons, muted copy */
  --text-detail: 0.8125rem;    /* 13px: help text, status lines, data values */
  --text-micro: 0.75rem;       /* 12px: uppercase micro-headers, status detail */

  /* Quasar override */
  --q-primary: var(--color-accent);
}

body {
  font-family: var(--font-ui);
  font-size: var(--text-body);
  line-height: 1.5;
  color: var(--color-text-main);
  background-color: var(--color-background);
  -webkit-font-smoothing: antialiased;
  --q-primary: var(--color-accent) !important;
  --q-positive: var(--color-success) !important;
  --q-negative: var(--color-error) !important;
  --q-warning: var(--color-warning) !important;
}

/* --- Typography — Helvetica Neue, one size per role, weight/case carry sub-roles --- */

.demo-page-title {
  font-family: var(--font-ui);
  font-weight: 700;
  font-size: var(--text-page-title);
  line-height: 1.05;
  letter-spacing: -0.02em;
  color: var(--color-ink);
    padding-top: var(--space-3);
  padding-bottom: var(--space-3);
  border-bottom: 3px solid var(--color-rule-strong);
  margin: 0;
}

.demo-brand-label {
  font-weight: 600;
  font-size: var(--text-label);
  line-height: 1.1;
  letter-spacing: 0.04em;
  color: var(--color-ink-secondary);
  margin-top: 0;
  text-align: center;
}

.demo-brand-lockup {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

.demo-supporting {
  font-weight: 400;
  font-size: var(--text-label);
  line-height: 1.5;
  color: var(--color-text-secondary);
}

.demo-section-heading {
  font-weight: 700;
  font-size: var(--text-section);
  line-height: 1.25;
  letter-spacing: -0.01em;
  color: var(--color-ink);
  margin: 0;
}

.demo-component-heading {
  font-weight: 700;
  font-size: var(--text-label);
  line-height: 1.4;
  color: var(--color-ink);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin: 0;
}

.demo-avatar {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-md);
  object-fit: cover;
  flex-shrink: 0;
}

.demo-label {
  font-weight: 500;
  font-size: var(--text-label);
  line-height: 1.4;
  color: var(--color-text-main);
}

.demo-body {
  font-weight: 400;
  font-size: var(--text-body);
  line-height: 1.5;
  color: var(--color-text-main);
}

/* --- Cards — white panels on paper, hairline rules, no shadow --- */

.q-card.demo-card {
  background-color: var(--color-surface) !important;
  border-radius: var(--radius) !important;
  border: 1px solid var(--color-border) !important;
  box-shadow: none !important;
  padding: var(--space-6) !important;
}

/* --- Buttons --- */

/* Primary — violet block, sharp Swiss radius */
.q-btn.demo-btn-primary,
.q-btn.demo-btn-primary.bg-primary,
.bg-primary.demo-btn-primary {
  background: var(--color-accent) !important;
  color: var(--color-text-on-primary) !important;
  font-family: var(--font-ui);
  font-weight: 700;
  font-size: var(--text-body);
  line-height: 1.4;
  border-radius: var(--radius-sm) !important;
  padding: var(--space-2) var(--space-8);
  transition: background-color 0.15s ease-out;
  box-shadow: none !important;
  text-transform: none !important;
}
.q-btn.demo-btn-primary:hover:not(.disabled) {
  background-color: var(--color-accent-hover) !important;
}
.q-btn.demo-btn-primary.disabled {
  background-color: var(--color-rule) !important;
  color: var(--color-text-secondary) !important;
  opacity: 1 !important;
}

/* Secondary sample buttons — transparent until hover, quieter than the primary action */
.q-btn.demo-btn-secondary,
.q-btn.demo-btn-secondary.text-primary {
  font-family: var(--font-ui);
  font-weight: 600;
  font-size: var(--text-body);
  line-height: 1.4;
  color: var(--color-sample-button-text) !important;
  background: transparent !important;
  background-color: transparent !important;
  border: 1px solid var(--color-sample-button) !important;
  border-radius: var(--radius-sm) !important;
  padding: var(--space-2) var(--space-4);
  box-shadow: none !important;
  text-transform: none !important;
  transition:
    background-color 0.15s ease-out,
    border-color 0.15s ease-out,
    color 0.15s ease-out;
}
.q-btn.demo-btn-secondary:hover,
.q-btn.demo-btn-secondary.text-primary:hover {
  background-color: var(--color-sample-button) !important;
  border-color: transparent !important;
  color: var(--color-ink) !important;
}

/* --- Toggle / strategy --- */

.demo-strategy-desc {
  font-weight: 400;
  font-size: var(--text-detail);
  line-height: 1.5;
  color: var(--color-text-secondary);
}

.demo-strategy-radio {
  --q-primary: var(--color-ink) !important;
  padding: 0.25rem 0;
}

.demo-strategy-radio .q-radio {
  align-items: center;
}

.demo-strategy-radio .q-radio__label {
  font-family: var(--font-sans) !important;
  font-size: var(--text-body) !important;
  font-weight: 500 !important;
  color: var(--color-text-primary) !important;
  text-transform: none !important;
  margin-left: 0.5rem;
}

.demo-strategy-radio .q-radio__inner {
  color: var(--color-ink) !important;
}

.demo-prompt-card {
  display: flex !important;
  flex-direction: column;
  min-height: 42rem;
}

.demo-prompt-input {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
}

.demo-prompt-input .q-field__inner,
.demo-prompt-input .q-field__control {
  display: flex;
  flex: 1 1 auto;
  min-height: 26rem;
}

.demo-prompt-input .q-field__control-container {
  min-height: inherit;
}

.demo-prompt-input .q-field__native,
.demo-prompt-input textarea {
  min-height: 26rem !important;
  max-height: none !important;
  overflow-y: hidden;
  resize: vertical;
}

.demo-strategy-select.q-field--focused .q-field__control {
  box-shadow: inset 0 -2px 0 var(--color-ink) !important;
}

.demo-strategy-select .q-field__control::after {
  background: var(--color-ink) !important;
}

.demo-strategy-menu .q-item--active,
.demo-strategy-menu .q-item--focused {
  color: var(--color-ink) !important;
  background-color: var(--color-surface-alt) !important;
}

/* --- Response panel --- */

.demo-response-text {
  font-weight: 400;
  font-size: var(--text-body);
  color: var(--color-text-main);
  line-height: 1.6;
  max-width: 68ch;
  white-space: pre-wrap;
  word-break: break-word;
}

.demo-response-output {
  flex: 1 1 auto;
  overflow-y: auto;
  padding-right: var(--space-2);
  scrollbar-color: var(--color-rule) transparent;
  scrollbar-width: thin;
}

.demo-response-card {
  display: flex !important;
  flex-direction: column;
  min-height: 42rem;
}

/* The ui.refreshable wrapper inside the response card must flex to fill */
.demo-response-card > .nicegui-refreshable {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
}

.demo-response-status {
  font-weight: 500;
  font-size: var(--text-detail);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.demo-response-status--success { color: var(--color-success); }
.demo-response-status--error { color: var(--color-error); }
.demo-response-status--streaming { color: var(--color-accent); }

/* --- Evaluation scores table --- */

.demo-scores-card {
  display: flex !important;
  flex-direction: column;
}

.demo-scores-heading {
  margin-bottom: var(--space-4);
}

.demo-score-comment {
  max-width: 24rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.demo-score-value--pass { color: var(--color-success); font-weight: 600; }
.demo-score-value--fail { color: var(--color-error); font-weight: 600; }

.demo-scores-empty {
  font-weight: 400;
  font-size: var(--text-detail);
  color: var(--color-text-secondary);
}

.demo-scores-spinner {
  color: var(--color-accent);
}

.demo-scores-meta {
  font-weight: 400;
  font-size: var(--text-detail);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-3);
}

.demo-scores-table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  font-family: var(--font-ui);
  font-size: var(--text-detail);
}

.demo-scores-table th {
  text-align: left;
  font-weight: 600;
  font-size: var(--text-micro);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-secondary);
  padding: var(--space-2) var(--space-3);
  border-bottom: 2px solid var(--color-rule-strong);
}

.demo-scores-table td {
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-main);
  vertical-align: top;
}

.demo-scores-table td.demo-score-cell--mono {
  font-family: var(--font-mono);
  font-size: var(--text-micro);
}

.demo-scores-table td.demo-score-cell--truncate {
  max-width: 16rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* --- Status bar — black instrument strip --- */

.demo-status-bar {
  display: flex;
  gap: var(--space-2);
  font-family: var(--font-ui);
  font-weight: 600;
  font-size: var(--text-body);
  background: transparent !important;
  background-color: transparent !important;
  border: 1px solid var(--color-accent) !important;
  border-radius: var(--radius-sm) !important;
  padding: var(--space-2) var(--space-4);
}

.demo-status-bar .q-btn__content {
  gap: var(--space-2);
}


.demo-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.demo-status-dot--ready { background-color: #4ADE80; }
.demo-status-dot--warning { background-color: #FBBF24; }



/* --- Section divider --- */

.demo-section-divider {
  height: 1px;
  background-color: var(--color-border);
  margin: var(--space-3) 0;
}

/* --- Tabs --- */

/* --- Browser surfaces --- */

*:focus-visible {
  outline: 2px solid var(--color-accent) !important;
  outline-offset: 2px;
}

.q-focusable:focus,
.q-btn:focus,
.q-field__native:focus {
  outline: 2px solid var(--color-accent) !important;
  outline-offset: 3px;
}

.q-btn:focus {
  box-shadow: 0 0 0 2px var(--color-surface), 0 0 0 4px var(--color-accent) !important;
}

.q-field__native:focus {
  box-shadow: inset 0 -2px 0 var(--color-accent) !important;
}

.q-field--focused .q-field__control {
  box-shadow: 0 0 0 2px var(--color-accent) !important;
}

.q-btn.disabled:focus,
.q-btn[disabled]:focus {
  outline: none !important;
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
    return format_trace(value, unavailable=_UNAVAILABLE_COPY)


def _format_cost(value: float | Unavailable) -> str:
    return format_cost(value, unavailable=_COST_UNAVAILABLE_COPY)


def _html_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _strategy_with_model(strategy: RoutingStrategy, model_id: str) -> RoutingStrategy:
    return replace(strategy, model=model_id)


def _heading(text: str, *, level: int, classes: str) -> None:
    ui.html(text, tag=f"h{level}").classes(classes)


@dataclass(frozen=True)
class SamplePrompt:
    label: str
    prompt: str


SAMPLE_PROMPTS = (
    SamplePrompt(
        label="Draft timeout reply",
        prompt="Write a concise customer-support reply to this API reliability complaint. Lead by acknowledging the launch-window impact before any explanation. Ask for at least two concrete diagnostics, give a next step with an owner or timeframe, and do not promise this will never happen again.\n\nCustomer message:\nYour API timed out during our launch window and now my team is getting blamed. We need answers. We had three separate windows this morning where calls just hung until our client-side timeout fired at 30s. This was the one day of the quarter we could not afford it. What actually happened?",
    ),
    SamplePrompt(
        label="Handle renewal risk",
        prompt="Write a concise customer-support reply to this API reliability complaint. Address the renewal risk directly without offering discounts or guarantees. Acknowledge that the earlier resolution failed, ask for the current incident details, and give the customer something concrete they can take to their CTO.\n\nCustomer message:\nThis is the second time in a month. Last time we were told it was investigated and resolved. It clearly wasn't. I have a renewal conversation next week and right now I can't defend keeping you. What do I tell my CTO?",
    ),
)

EVAL_SCENARIO = (
    "Handling API reliability complaints can be complex and time-consuming. Support teams often struggle to triage issues quickly, draft effective responses, and provide actionable feedback to product teams.  \n\n This slows down resolution times and impacts customer satisfaction."
    "Imagine an AI assistant that instantly drafts thoughtful, impact-aware support replies—acknowledging customer pain points without defensiveness, requesting clear diagnostics, and offering honest next steps. \n\n Ishlab's demo showcases exactly that, helping support staff move faster and smarter."
)

EVAL_DESCRIPTION = (
    "An angry customer says the API keeps failing and hints they're ready to leave.\n"
    "\n"
    "We score whether the reply holds up.\n"
    "\n"
    "Leads with the customer's problem — names what they actually lost, before any explanation or caveat.\n\n"
    "Asks for real detail — request IDs, timestamps, endpoints. Not 'send more info.'\n\n"
    "Commits to a next step — what happens, who does it, by when.\n\n"
    "Promises only what we can keep — no 'this wont happen again, no unauthorized credits.'\n\n"
    "Doesn't guess at blame — no pointing at the customer's code before the evidence is in.\n\n"
    "Gets the scope right — doesn't inflate a hiccup into an outage, or wave off a real one.\n\n"
    "Answers the churn signal — addresses 'we are evaluating alternatives' directly, without pleading."
)


EMPTY_RESPONSE = "Waiting for prompt to run"
STREAMING_RESPONSE = "Streaming from OpenRouter..."
SUCCESS_RESPONSE = "Request completed successfully."
FAILURE_RESPONSE = "Request failed."


@dataclass
class _UIState:
    is_running: bool = False
    last_run: InferenceRun | None = None
    response: str = ""
    response_status: str = EMPTY_RESPONSE
    is_fetching_scores: bool = False
    scores: tuple[LangfuseScore, ...] | None = None
    scores_fetch_status: str = ""
    current_trace_id: str | None = None
    current_observation_id: str | None = None
    observation_details: ObservationDetails | None = None


async def _run_inference(
    prompt: str,
    *,
    api_key: str,
    history: SQLiteRunHistory,
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
            observation_id: str | None = None
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
                observation_id = outcome.observation_id

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
                observation_id=observation_id,
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


def build_app(
    config: AppConfig,
    history: SQLiteRunHistory,
    *,
    stream_fn: StreamFn = stream_chat_completion,
) -> None:
    ui.page_title("ishlab Production Inference Lab")
    ui.add_head_html('<link rel="icon" href="assets/favicon.ico" type="image/x-icon">')
    state = _UIState()
    initial_strategy_name = next(iter(STRATEGIES))

    # Mount static assets for avatar and logo
    assets_dir = Path(__file__).parent.parent.parent / "assets"
    if assets_dir.exists():
        ng_app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    def sync_run_button() -> None:
        disabled = (
            not config.openrouter_ready
            or state.is_running
            or not str(prompt.value or "").strip()
            or not str(strategy_select.value or "").strip()
        )
        if disabled:
            run_button.disable()
        else:
            run_button.enable()

    @ui.refreshable
    def response_panel() -> None:
        _heading("LLM Response", level=2, classes="demo-section-heading")
        status_class = "demo-response-status"
        if state.is_running:
            status_class += " demo-response-status--streaming"
        elif state.last_run is not None:
            if state.last_run.status in (Status.SUCCEEDED, Status.FALLBACK_SUCCEEDED):
                status_class += " demo-response-status--success"
            else:
                status_class += " demo-response-status--error"
        ui.label(state.response_status).classes(status_class)
        with ui.element("div").classes("demo-response-output"):
            ui.label(state.response or EMPTY_RESPONSE).classes("demo-response-text")

    def refresh(panel: object) -> None:
        cast(Any, panel).refresh()

    @ui.refreshable
    def eval_scores_panel() -> None:
        if not config.langfuse_ready:
            ui.label(
                "Langfuse tracing is not configured. Set LANGFUSE_PUBLIC_KEY, "
                "LANGFUSE_SECRET_KEY, and LANGFUSE_BASE_URL to fetch evaluation scores."
            ).classes("demo-scores-empty")
            return
        if state.is_fetching_scores:
            with ui.row().classes("items-center gap-2"):
                ui.spinner(size="1.25rem").classes("demo-scores-spinner")
                ui.label("Waiting for trace scores…").classes("demo-scores-empty")
            return
        if state.scores_fetch_status == "failed":
            ui.label("Failed to fetch scores.").classes("demo-scores-empty")
            return
        if state.scores is None:
            ui.label("Run inference to load evaluation scores from Langfuse.").classes(
                "demo-scores-empty"
            )
            return
        if not state.scores:
            ui.label(
                "No evaluation scores found yet. Run inference to generate traces, "
                "then wait for Langfuse evaluator jobs to score them."
            ).classes("demo-scores-empty")
            return

        if state.observation_details is not None:
            details = state.observation_details
            detail_parts: list[str] = []
            if details.model_name:
                detail_parts.append(f"Model: {_html_escape(details.model_name)}")
            if details.latency_ms is not None:
                detail_parts.append(f"Latency: {details.latency_ms:.0f} ms")
            if details.model_parameters:
                params = ", ".join(f"{k}={v}" for k, v in details.model_parameters.items())
                detail_parts.append(f"Params: {_html_escape(params)}")
            if detail_parts:
                ui.label(" · ".join(detail_parts)).classes("demo-scores-meta")

        rows_html: list[str] = []
        for score in state.scores:
            value_class = ""
            if score.data_type == "BOOLEAN":
                value_class = (
                    "demo-score-value--pass" if bool(score.value) else "demo-score-value--fail"
                )
            trace_label = f"{score.trace_id[:8]}…" if score.trace_id else "—"
            trace_title = score.trace_id or ""
            comment_title = score.comment or ""
            name_cell = (
                f'<td class="demo-score-cell--truncate" title="{_html_escape(comment_title)}">'
                f"{_html_escape(score.name)}</td>"
            )
            value_cell = f'<td class="{value_class}">{_html_escape(score.display_value)}</td>'
            trace_cell = (
                f'<td class="demo-score-cell--mono" title="{_html_escape(trace_title)}">'
                f"{_html_escape(trace_label)}</td>"
            )
            rows_html.append(
                "<tr>"
                + name_cell
                + f"<td>{_html_escape(score.data_type)}</td>"
                + value_cell
                + trace_cell
                + f'<td class="demo-score-cell--mono">{_html_escape(score.timestamp)}</td>'
                + "</tr>"
            )

        table_html = (
            '<table class="demo-scores-table"><colgroup>'
            '<col style="width: 30%"><col style="width: 15%"><col style="width: 15%">'
            '<col style="width: 20%"><col style="width: 20%"></colgroup>'
            "<thead><tr>"
            "<th>Name</th><th>Type</th><th>Value</th><th>Trace</th><th>Timestamp</th>"
            "</tr></thead><tbody>" + "".join(rows_html) + "</tbody></table>"
        )
        ui.html(table_html).classes("w-full")

    async def fetch_scores_handler() -> None:
        if not config.langfuse_ready or state.is_fetching_scores:
            return
        state.is_fetching_scores = True
        refresh(eval_scores_panel)
        scores: tuple[LangfuseScore, ...] = ()
        status = "enabled"
        if state.current_observation_id:
            prev_count = -1
            for _ in range(10):
                outcome = await fetch_langfuse_scores(
                    config,
                    limit=50,
                    trace_id=state.current_trace_id,
                    observation_id=state.current_observation_id,
                )
                status = outcome.status
                if outcome.status != "enabled":
                    break
                scores = outcome.scores or ()
                if scores and len(scores) == prev_count:
                    break
                prev_count = len(scores)
                await asyncio.sleep(3)
        state.scores = scores
        state.scores_fetch_status = status
        state.observation_details = await fetch_observation_details(
            config, observation_id=state.current_observation_id or ""
        )
        state.is_fetching_scores = False
        refresh(eval_scores_panel)

    async def run_request() -> None:
        if not config.openrouter_ready or state.is_running:
            return
        prompt_text = str(prompt.value or "").strip()
        selected_strategy = STRATEGIES.get(strategy_select.value, INTELLIGENCE_STRATEGY)
        model_id = model_select.value or STRATEGY_MODELS[selected_strategy.name][0]
        if not prompt_text or not model_id:
            sync_run_button()
            return

        state.is_running = True
        state.response = ""
        state.response_status = STREAMING_RESPONSE
        sync_run_button()
        refresh(response_panel)

        async def observed_stream(
            prompt_value: str, **kwargs: object
        ) -> AsyncIterator[StreamChunk | StreamedResult]:
            async for event in stream_fn(prompt_value, **kwargs):
                if isinstance(event, StreamChunk):
                    state.response = state.response + event.text_delta
                    refresh(response_panel)
                yield event

        selected_strategy = _strategy_with_model(
            selected_strategy,
            model_id,
        )
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
        state.current_trace_id = run.telemetry.trace_id if run.telemetry else None
        state.current_observation_id = run.telemetry.observation_id if run.telemetry else None
        state.observation_details = None
        state.response = run.streamed_text
        if run.status in (Status.SUCCEEDED, Status.FALLBACK_SUCCEEDED):
            state.response_status = SUCCESS_RESPONSE
        else:
            state.response_status = FAILURE_RESPONSE
        sync_run_button()
        refresh(response_panel)
        await fetch_scores_handler()

    def fill_prompt(value: str) -> None:
        prompt.value = value
        sync_run_button()

    with ui.column().classes("mx-auto w-full max-w-[1280px] gap-6 p-6"):
        ui.add_head_html(_DESIGN_CSS)

        # Header: compact brand lockup inline-left of big title
        with ui.column().classes("gap-0 w-full"), ui.row().classes("items-start gap-4"):
            with ui.column().classes("demo-brand-lockup"):
                ui.image("/assets/ish-avatar.png").classes("demo-avatar").props('alt=""')
                ui.label("ishlab").classes("demo-brand-label")
            _heading("Production Inference Lab", level=1, classes="demo-page-title")

        ui.label(
            "The app runs live streaming inference, exposes routing, cost, latency, token, and trace evidence, and runs a three-to-five-case deterministic eval set. "
        ).classes("text-body")
        ui.label(
            "This demo shows what changes when inference becomes something you have to operate in production: routing, latency, cost, traces, and evals."
        ).classes("text-body")

        # Request panel with section dividers
        with ui.card().classes("w-full demo-card"):
            _heading(
                "Prompt routing, traceability, and evaluation come together for meaningful production inference",
                level=3,
                classes="text-xl font-semibold pb-4",
            )
            with ui.splitter() as splitter:
                with splitter.before:
                    _heading(
                        "Prompt Evaluation Scenario", level=5, classes="text-base font-semibold"
                    )
                    # ui.html preserves the \n line breaks via whitespace-pre-line
                    ui.html(EVAL_SCENARIO).classes("pr-6 text-body").style("white-space: pre-line;")
                with splitter.after:
                    _heading("Prompt Evaluation", level=5, classes="pl-6 text-base font-semibold")
                    ui.html(EVAL_DESCRIPTION).classes("pl-6 text-body").style(
                        "white-space: pre-line;"
                    )

        def _status_item(label: str, ready: bool, detail: str) -> None:
            dot_class = "demo-status-dot--ready" if ready else "demo-status-dot--warning"

            with ui.button().props("outline").classes("demo-status-bar").props(
                f'aria-label="{label}: {detail}"'
            ):
                ui.element("span").classes(f"demo-status-dot {dot_class}")
                ui.label(label)

        # Compact inline status bar
        with (
            ui.element("div")
            .classes("w-full flex items-center gap-4 flex-wrap")
            .props('role="status" aria-label="Credential status"')
        ):
            _status_item(
                "OpenRouter",
                config.openrouter_ready,
                "Required credential is present; value is not displayed."
                if config.openrouter_ready
                else "Export OPENROUTER_API_KEY before live inference.",
            )
            _status_item(
                "Langfuse tracing",
                config.langfuse_ready,
                "Optional tracing credentials are present; values are not displayed."
                if not config.langfuse_ready
                else "Required credential is present; value is not displayed.",
            )

        with ui.row().classes("w-full items-stretch gap-6 flex-wrap"):
            with ui.card().classes("flex-1 demo-card demo-prompt-card"):
                _heading("Prompt", level=2, classes="demo-section-heading")
                prompt = (
                    ui.textarea(
                        placeholder="Draft or revise a support reply to an API reliability complaint...",
                        on_change=lambda _: sync_run_button(),
                    )
                    .classes("w-full demo-prompt-input")
                    .props('aria-label="Prompt" autogrow rows=18')
                )
                ui.label("Sample prompt").classes("demo-label")
                with ui.row().classes("w-full gap-2 flex-wrap"):
                    for sample in SAMPLE_PROMPTS:
                        ui.button(
                            sample.label,
                            on_click=lambda sample=sample: fill_prompt(sample.prompt),
                        ).props("flat").classes("demo-btn-secondary").style(
                            "--q-primary: var(--color-sample-button-text);"
                        )

                    ui.element("div").classes("demo-section-divider")

                _heading("Strategy", level=2, classes="demo-component-heading")
                strategy_select = (
                    ui.radio(
                        options={
                            s.name: ROUTING_STRATEGY_LABELS[s.name]
                            for s in STRATEGIES.values()
                        },
                        value=initial_strategy_name,
                    )
                    .props('aria-label="Routing strategy"')
                    .classes("demo-strategy-radio")
                    .style("--q-primary: var(--color-ink);")
                )
                strategy_description_label = ui.label(
                    STRATEGIES[initial_strategy_name].description
                ).classes("demo-strategy-desc")

                initial_strategy_models = STRATEGY_MODELS[initial_strategy_name]
                model_select = (
                    ui.select(
                        options={
                            m: STRATEGY_MODEL_SHORT_NAMES[m] for m in initial_strategy_models
                        },
                        label="Model",
                        value=initial_strategy_models[0],
                    )
                    .props('aria-label="Routing model"')
                    .classes("demo-model-select")
                )

                def update_strategy_display(_: object) -> None:
                    selected = STRATEGIES.get(strategy_select.value, INTELLIGENCE_STRATEGY)
                    strategy_description_label.text = selected.description
                    new_models = STRATEGY_MODELS[selected.name]
                    model_select.options = {
                        m: STRATEGY_MODEL_SHORT_NAMES[m] for m in new_models
                    }
                    model_select.value = new_models[0]
                    model_select.update()
                    sync_run_button()

                strategy_select.on("update:model-value", update_strategy_display)

                ui.element("div").classes("demo-section-divider")

                ui.element("div").classes("demo-section-divider")

                with ui.column().classes("gap-1"):
                    run_button = (
                        ui.button("Run Inference", on_click=run_request)
                        .classes("demo-btn-primary")
                        .props("unelevated")
                        .style("--q-primary: var(--color-accent);")
                    )
                    run_button.disable()

            with ui.card().classes("flex-1 demo-card demo-response-card"):
                response_panel()

        with ui.card().classes("w-full demo-card demo-scores-card"):
            _heading(
                "Evaluation Scores", level=2, classes="demo-section-heading demo-scores-heading"
            )
            eval_scores_panel()
