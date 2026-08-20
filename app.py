import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from nicegui import app as ng_app
from nicegui import ui

from openrouter_demo.config import load_config
from openrouter_demo.ui import build_app


def main() -> None:
    config = load_config()
    # Use SQLite-backed run history for demo deployments (persist recent runs)
    from openrouter_demo.sqlite_store import SQLiteRunHistory

    history = SQLiteRunHistory(db_path="data/runs.db")
    build_app(config, history)

    # Health endpoint for platform readiness checks
    @ng_app.get("/health")
    def health():
        return {
            "status": "ok" if config.openrouter_ready else "degraded",
            "openrouter_ready": config.openrouter_ready,
            "langfuse_ready": config.langfuse_ready,
        }

    ui.run(title="OpenRouter Production Inference Lab", reload=False)


if __name__ == "__main__":
    main()
