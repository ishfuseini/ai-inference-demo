from typing import List, Optional
from nicegui import app as ng_app
from openrouter_demo.sqlite_store import SQLiteRunHistory
from openrouter_demo.models import InferenceRun


def _serialize_run(run: InferenceRun) -> dict:
    return {
        "run_id": run.run_id,
        "prompt": run.prompt,
        "strategy_name": run.strategy_name,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "status": run.status.value if run.status else None,
        "streamed_text": run.streamed_text,
        "error_message": run.error_message,
        "telemetry": run.telemetry.__dict__ if run.telemetry is not None else None,
    }


@ng_app.get("/api/runs")
def list_runs(limit: int = 50) -> List[dict]:
    store = SQLiteRunHistory()
    runs = store.all(limit=limit)
    return [_serialize_run(r) for r in runs]


@ng_app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> Optional[dict]:
    store = SQLiteRunHistory()
    run = store.get(run_id)
    if not run:
        return None
    return _serialize_run(run)


@ng_app.post("/api/runs/{run_id}/replay")
def replay_run(run_id: str) -> Optional[dict]:
    """Return the run payload needed to replay the run client-side (prompt + strategy)."""
    store = SQLiteRunHistory()
    run = store.get(run_id)
    if not run:
        return None
    return {"prompt": run.prompt, "strategy": run.strategy_name}
