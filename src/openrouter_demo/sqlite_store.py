import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

from openrouter_demo.models import (
    InferenceRun,
    Status,
    TelemetryEvidence,
)


class SQLiteRunHistory:
    def __init__(self, db_path: str = "data/runs.db", max_runs: int = 500):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._max_runs = max_runs
        # Allow connections from other threads but guard access with a lock
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    prompt TEXT,
                    strategy_name TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    status TEXT,
                    streamed_text TEXT,
                    error_message TEXT,
                    telemetry_json TEXT
                )
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_started_at ON runs(started_at DESC)")
            self._conn.commit()

    def append(self, run: InferenceRun) -> None:
        payload = {
            "telemetry": run.telemetry.to_dict() if run.telemetry is not None else None,
        }
        telemetry_json = json.dumps(payload)
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "REPLACE INTO runs (run_id, prompt, strategy_name, started_at, completed_at, status, streamed_text, error_message, telemetry_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run.run_id,
                    run.prompt,
                    run.strategy_name,
                    run.started_at.isoformat() if run.started_at else None,
                    run.completed_at.isoformat() if run.completed_at else None,
                    run.status.value if isinstance(run.status, Status) else str(run.status),
                    run.streamed_text,
                    run.error_message,
                    telemetry_json,
                ),
            )
            self._conn.commit()
            # enforce max runs: delete any runs older than the most recent `_max_runs`
            cur.execute(
                "SELECT run_id FROM runs ORDER BY started_at DESC LIMIT -1 OFFSET ?",
                (self._max_runs,),
            )
            rows = cur.fetchall()
            if rows:
                ids_to_delete = [r["run_id"] for r in rows]
                cur.executemany("DELETE FROM runs WHERE run_id = ?", [(i,) for i in ids_to_delete])
                self._conn.commit()

    def all(self, limit: int | None = None) -> list[InferenceRun]:
        with self._lock:
            cur = self._conn.cursor()
            q = "SELECT * FROM runs ORDER BY started_at DESC"
            if limit:
                q += " LIMIT ?"
                rows = cur.execute(q, (limit,)).fetchall()
            else:
                rows = cur.execute(q).fetchall()
            return [self._row_to_run(r) for r in rows]

    def get(self, run_id: str) -> InferenceRun | None:
        with self._lock:
            cur = self._conn.cursor()
            row = cur.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
            if not row:
                return None
            return self._row_to_run(row)

    def _row_to_run(self, row: sqlite3.Row) -> InferenceRun:
        telemetry = None
        if row["telemetry_json"]:
            doc = json.loads(row["telemetry_json"])
            if isinstance(doc, dict) and doc.get("telemetry") is not None:
                telemetry = TelemetryEvidence.from_dict(doc["telemetry"])
        started_at = datetime.fromisoformat(row["started_at"]) if row["started_at"] else None
        completed_at = datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
        status = Status(row["status"]) if row["status"] else Status.FAILED
        return InferenceRun(
            run_id=row["run_id"],
            prompt=row["prompt"],
            strategy_name=row["strategy_name"],
            started_at=started_at,
            completed_at=completed_at,
            status=status,
            streamed_text=row["streamed_text"],
            error_message=row["error_message"],
            telemetry=telemetry,
        )
