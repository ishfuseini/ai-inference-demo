from __future__ import annotations

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
from openrouter_demo.formatting import format_cost, format_latency, format_number, format_trace
from openrouter_demo.config import OPENROUTER_API_KEY, AppConfig
from openrouter_demo.models import (
    UNAVAILABLE,
    InferenceRun,
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
from openrouter_demo.telemetry import record_trace

type StreamFn = Callable[..., AsyncIterator[StreamChunk | StreamedResult]]


_UNAVAILABLE_COPY = "Unavailable from selected route/provider."
_COST_UNAVAILABLE_COPY = "Cost metadata was not returned for this route/provider."
_LATENCY_UNAVAILABLE_COPY = "Latency was not returned for this route/provider."
_WAITING_COPY = "Waiting"

STRATEGY_MODEL_OPTIONS: dict[str, tuple[str, ...]] = {
    "cost": (
        "nvidia/nemotron-3.5-lightning:free",
        "google/gemma-4-31b-it:free",
        "openai/gpt-oss-20b:free",
    ),
    "latency": (
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        "poolside/laguna-xs-2.1:free",
        "google/gemma-4-26b-a4b-it:free",
    ),
    "intelligence": (
        "anthropic/claude-opus-5",
        "openai/gpt-5.6-sol",
        "moonshotai/kimi-k3",
    ),
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
  --color-accent: #8A2BE2;
  --color-accent-hover: #6E21B8;
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
  --color-border: var(--color-rule);
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

.demo-title-with-logo {
  display: flex;
  align-items: baseline;
  gap: var(--space-4);
}

.demo-subtitle {
  font-weight: 500;
  font-size: var(--text-body);
  line-height: 1.5;
  color: var(--color-ink);
  margin-top: var(--space-3);
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

/* Setup banner — warning on paper, strong black rule instead of color edge */
.q-card.demo-setup-banner {
  background-color: var(--color-warning-bg) !important;
  border-radius: var(--radius) !important;
  border: 1px solid var(--color-rule) !important;
  box-shadow: none !important;
  padding: var(--space-4) var(--space-6) !important;
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
  font-size: var(--text-micro);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.demo-telemetry-value {
  font-family: var(--font-mono);
  font-weight: 400;
  font-size: var(--text-detail);
  color: var(--color-text-main);
  text-align: right;
  max-width: 65%;
  word-break: break-word;
}

/* --- History grid --- */

.demo-grid-scroll {
  overflow-x: auto;
  width: 100%;
  padding-bottom: var(--space-2);
  scrollbar-color: var(--color-rule) transparent;
  scrollbar-width: thin;
}

.demo-grid-scroll::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}

.demo-grid-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.demo-grid-scroll::-webkit-scrollbar-thumb {
  background: var(--color-rule);
  border-radius: 0;
}

.demo-grid-scroll::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-secondary);
}

.demo-grid-scroll .nicegui-grid {
  width: max-content;
  min-width: 100%;
}

.demo-grid-header {
  font-weight: 500;
  font-size: var(--text-micro);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: var(--space-2) var(--space-3);
  border-bottom: 2px solid var(--color-border);
  white-space: nowrap;
}

.demo-grid-cell {
  font-family: var(--font-mono);
  font-weight: 400;
  font-size: var(--text-detail);
  color: var(--color-text-main);
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.demo-grid-link,
.demo-grid-link:visited {
  color: var(--color-ink);
  text-decoration: underline;
  text-decoration-color: var(--color-accent);
  text-decoration-thickness: 1px;
  text-underline-offset: 2px;
}

.demo-grid-link:hover {
  color: var(--color-accent);
}

.demo-cell-tooltip {
  font-family: var(--font-mono);
  font-size: var(--text-detail);
  background-color: var(--color-text-main);
  color: var(--color-surface);
  border-radius: var(--radius);
  padding: var(--space-1) var(--space-2);
  max-width: 320px;
  word-break: break-all;
}

/* --- Toggle / strategy --- */

.demo-toggle-help {
  font-weight: 400;
  font-size: var(--text-detail);
  line-height: 1.5;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

.demo-strategy-desc {
  font-weight: 400;
  font-size: var(--text-detail);
  line-height: 1.5;
  color: var(--color-text-secondary);
}

.demo-strategy-select {
  --q-primary: var(--color-ink) !important;
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

.demo-toggle-row .q-checkbox__label {
  font-weight: 500;
  font-size: var(--text-label);
  line-height: 1.4;
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
  min-height: 16rem;
  max-height: 32rem;
  overflow-y: auto;
  padding-right: var(--space-2);
  scrollbar-color: var(--color-rule) transparent;
  scrollbar-width: thin;
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

/* --- Status bar — black instrument strip --- */

.demo-status-bar {
  display: flex;
  align-items: center;
  gap: var(--space-8);
  padding: var(--space-3) var(--space-6);
  background-color: var(--color-ink);
  border-radius: var(--radius-sm);
  border: none;
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

.demo-status-dot--ready { background-color: #4ADE80; }
.demo-status-dot--warning { background-color: #FBBF24; }

.demo-status-item-label {
  font-weight: 500;
  font-size: var(--text-detail);
  color: #FFFFFF;
}

.demo-status-item-detail {
  font-weight: 400;
  font-size: var(--text-micro);
  color: rgba(255, 255, 255, 0.62);
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
  font-size: var(--text-label);
  text-transform: none;
  color: var(--color-text-secondary);
  padding: var(--space-2) var(--space-4);
  min-height: 40px;
}

.demo-tabs .q-tab--active {
  color: var(--color-ink);
}

.demo-tabs .q-tab__indicator {
  background-color: var(--color-ink);
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
  outline: 2px solid var(--color-accent) !important;
  outline-offset: 2px;
}

.q-focusable:focus,
.q-btn:focus,
.q-field__native:focus,
.q-toggle:focus,
.q-tab:focus {
  outline: 2px solid var(--color-accent) !important;
  outline-offset: 3px;
}

.q-btn:focus,
.q-toggle:focus,
.q-tab:focus {
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


def _format_tokens(value: int | Unavailable) -> str:
    return format_number(value, unavailable=_UNAVAILABLE_COPY)


def _format_latency(value: int | Unavailable) -> str:
    return format_latency(value, unavailable=_LATENCY_UNAVAILABLE_COPY)


def _format_cost(value: float | Unavailable) -> str:
    return format_cost(value, unavailable=_COST_UNAVAILABLE_COPY)


def _strategy_with_model(strategy: RoutingStrategy, model_id: str) -> RoutingStrategy:
    return replace(strategy, model=model_id)


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
    "Handling API reliability complaints can be complex and time-consuming. Support teams often struggle to triage issues quickly, draft effective responses, and provide actionable feedback to product teams. This slows down resolution times and impacts customer satisfaction."
    "Imagine an AI assistant that instantly drafts thoughtful, impact-aware support replies—acknowledging customer pain points without defensiveness, requesting clear diagnostics, and offering honest next steps. Ishlab’s demo showcases exactly that, helping support staff move faster and smarter."
)

EVAL_PROOF = (
    "Make It Reliable: Watch how routing preferences and graceful error handling keep your service steady, even under pressure.\n"
    "Make It Economical: Understand how different model choices impact cost, latency, and token usage—empowering you to optimize for price-performance balance.\n"
    "Make Changes Safely: Evaluate models side-by-side with quality scoring, traceability via Langfuse, and data-driven decision-making to pick the best fit for your need."
)
EVAL_DESCRIPTION = (
    "An angry customer says the API keeps failing and hints they're ready to leave.\n"
    "\n"
    "We score whether the reply holds up.\n"
    "\n"
    "Leads with the customer's problem — names what they actually lost, before any explanation or caveat.\n"
    "Asks for real detail — request IDs, timestamps, endpoints. Not 'send more info.'\n"
    "Commits to a next step — what happens, who does it, by when.\n"
    "Promises only what we can keep — no 'this wont happen again, no unauthorized credits.'\n"
    "Doesn't guess at blame — no pointing at the customer's code before the evidence is in.\n"
    "Gets the scope right — doesn't inflate a hiccup into an outage, or wave off a real one.\n"
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
    model_options: tuple[str, ...] = STRATEGY_MODEL_OPTIONS[initial_strategy_name]

    # Mount static assets for avatar and logo
    assets_dir = Path(__file__).parent.parent.parent / "assets"
    if assets_dir.exists():
        ng_app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    def sync_run_button() -> None:
        disabled = (
            not config.openrouter_ready
            or state.is_running
            or not str(prompt.value or "").strip()
            or not str(model_select.value or "").strip()
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

    async def run_request() -> None:
        if not config.openrouter_ready or state.is_running:
            return
        prompt_text = str(prompt.value or "").strip()
        model_id = str(model_select.value or "").strip()
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
            STRATEGIES.get(strategy_select.value, INTELLIGENCE_STRATEGY),
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
        state.response = run.streamed_text
        if run.status in (Status.SUCCEEDED, Status.FALLBACK_SUCCEEDED):
            state.response_status = SUCCESS_RESPONSE
        else:
            state.response_status = FAILURE_RESPONSE
        sync_run_button()
        refresh(response_panel)
        refresh(telemetry_panel)
        refresh(history_panel)
        refresh(comparison_panel)

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
        ).classes("demo-supporting")
        ui.label(
            "This demo shows what changes when inference becomes something you have to operate in production: routing, latency, cost, traces, and evals."
        ).classes("demo-supporting")

        # Request panel with section dividers
        with ui.card().classes("w-full demo-card"):
            _heading(
                "Experience how prompt routing, traceability, and evaluation come together",
                level=3,
                classes="text-section-heading",
            )
            _heading("Prompt Evaluation Scenario", level=5, classes="text-section-heading")
            # ui.html preserves the \n line breaks via whitespace-pre-line
            ui.html(EVAL_SCENARIO).classes("demo-body").style("white-space: pre-line;")
            _heading("Prompt Evaluation Description", level=5, classes="text-section-heading")
            ui.html(EVAL_DESCRIPTION).classes("demo-body").style("white-space: pre-line;")
            _heading(
                "Real-World Scenarios That Prove It Works", level=4, classes="text-section-heading"
            )
            ui.html(EVAL_PROOF).classes("demo-body").style("white-space: pre-line;")
            _heading("Eval Scorecard", level=4, classes="text-section-heading")

    def _status_item(label: str, ready: bool, detail: str) -> None:
        dot_class = "demo-status-dot--ready" if ready else "demo-status-dot--warning"
        short_detail = "Ready" if ready else "Needs setup"
        with ui.element("div").classes("demo-status-item").props(f'aria-label="{label}: {detail}"'):
            ui.element("div").classes(f"demo-status-dot {dot_class}")
            ui.label(label).classes("demo-status-item-label")
            ui.label(short_detail).classes("demo-status-item-label")

            # Compact inline status bar
        with (
            ui.element("div")
            .classes("demo-status-bar")
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

                _heading("Model Choice Strategy", level=2, classes="demo-component-heading")
                strategy_select = (
                    ui.select(
                        options={
                            s.name: ROUTING_STRATEGY_LABELS[s.name] for s in STRATEGIES.values()
                        },
                        value=initial_strategy_name,
                    )
                    .classes("w-full demo-strategy-select")
                    .props('aria-label="Routing strategy" popup-content-class=demo-strategy-menu')
                    .style("--q-primary: var(--color-ink);")
                )
                strategy_description_label = ui.label(
                    STRATEGIES[initial_strategy_name].description
                ).classes("demo-strategy-desc")

                def update_strategy_description(_: object) -> None:
                    selected = STRATEGIES.get(strategy_select.value, INTELLIGENCE_STRATEGY)
                    strategy_description_label.text = selected.description
                    model_select.options = STRATEGY_MODEL_OPTIONS[selected.name]
                    model_select.value = None
                    model_select.update()
                    sync_run_button()

                strategy_select.on("update:model-value", update_strategy_description)

                ui.element("div").classes("demo-section-divider")

                _heading("Model", level=2, classes="demo-component-heading")
                model_select = (
                    ui.select(
                        options=model_options,
                        value=None,
                    )
                    .classes("w-full demo-strategy-select")
                    .props('aria-label="Model" popup-content-class=demo-strategy-menu clearable')
                    .style("--q-primary: var(--color-ink);")
                )
                model_select.on("update:model-value", lambda _: sync_run_button())
                ui.label(
                    "Choose one of the three hard-coded models for the selected strategy."
                ).classes("demo-strategy-desc")

                ui.element("div").classes("demo-section-divider")

                with ui.column().classes("gap-1"):
                    run_button = (
                        ui.button("Run Inference", on_click=run_request)
                        .classes("demo-btn-primary")
                        .props("unelevated")
                        .style("--q-primary: var(--color-accent);")
                    )
                    run_button.disable()

            # Response panel (side by side with prompt card)
            with ui.card().classes("flex-1 demo-card"):
                response_panel()

        # Tabbed evidence: Telemetry + Run History + Comparison
        with ui.tabs().props("align=left").classes("w-full demo-tabs") as tabs:
            ui.tab("Telemetry")
            ui.tab("Run History")
            ui.tab("Comparison")
