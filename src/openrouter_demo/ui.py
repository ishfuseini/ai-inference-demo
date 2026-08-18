from nicegui import ui

from openrouter_demo.config import LANGFUSE_ENV_VARS, OPENROUTER_API_KEY, AppConfig


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
