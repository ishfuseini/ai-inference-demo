import json
import sqlite3
import threading
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from openrouter_demo.models import (
    AttemptRecord,
    FallbackEvidence,
    InferenceRun,
    RepeatObservation,
    Status,
    StreamedResult,
    TelemetryEvidence,
    deserialize_value,
)


def _deserialize(value: object) -> object:
    return deserialize_value(value)


def _attempt_from_dict(data: dict) -> AttemptRecord:
    return AttemptRecord(
        model=_deserialize(data.get("model")),
        provider=_deserialize(data.get("provider")),
        status=Status(data["status"]) if data.get("status") else Status.FAILED,
        error_message=data.get("error_message"),
        latency_ms=data.get("latency_ms") or 0,
        prompt_tokens=_deserialize(data.get("prompt_tokens")),
        completion_tokens=_deserialize(data.get("completion_tokens")),
        total_tokens=_deserialize(data.get("total_tokens")),
        cost_usd=_deserialize(data.get("cost_usd")),
    )


def _streamed_result_from_dict(data: dict) -> StreamedResult:
    return StreamedResult(
        text=data.get("text") or "",
        model=_deserialize(data.get("model")),
        provider=_deserialize(data.get("provider")),
        prompt_tokens=_deserialize(data.get("prompt_tokens")),
        completion_tokens=_deserialize(data.get("completion_tokens")),
        total_tokens=_deserialize(data.get("total_tokens")),
        cost_usd=_deserialize(data.get("cost_usd")),
        latency_ms=data.get("latency_ms") or 0,
        cache_status=_deserialize(data.get("cache_status")),
        cached_tokens=_deserialize(data.get("cached_tokens")),
        cache_write_tokens=_deserialize(data.get("cache_write_tokens")),
        openrouter_metadata=_deserialize(data.get("openrouter_metadata")),
    )


def _fallback_evidence_from_dict(data: dict) -> FallbackEvidence:
    return FallbackEvidence(
        primary=_attempt_from_dict(data["primary"]),
        fallback=_attempt_from_dict(data["fallback"]),
        simulated=bool(data.get("simulated", False)),
    )


def _repeat_observation_from_dict(data: dict) -> RepeatObservation:
    return RepeatObservation(
        first=_streamed_result_from_dict(data["first"]),
        second=_streamed_result_from_dict(data["second"]),
        cache_status=_deserialize(data.get("cache_status")),
        cached_tokens=_deserialize(data.get("cached_tokens")),
        cache_write_tokens=_deserialize(data.get("cache_write_tokens")),
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
            "fallback_evidence": asdict(run.fallback_evidence)
            if run.fallback_evidence is not None
            else None,
            "repeat_observation": asdict(run.repeat_observation)
            if run.repeat_observation is not None
            else None,
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
        fallback_evidence = None
        repeat_observation = None
        if row["telemetry_json"]:
            doc = json.loads(row["telemetry_json"])
            if doc is not None:
                if isinstance(doc, dict) and "telemetry" in doc:
                    if doc.get("telemetry") is not None:
                        telemetry = TelemetryEvidence.from_dict(doc["telemetry"])
                    if doc.get("fallback_evidence") is not None:
                        fallback_evidence = _fallback_evidence_from_dict(doc["fallback_evidence"])
                    if doc.get("repeat_observation") is not None:
                        repeat_observation = _repeat_observation_from_dict(doc["repeat_observation"])
                else:
                    telemetry = TelemetryEvidence(
                        model=doc.get("model"),
                        provider=doc.get("provider"),
                        latency_ms=doc.get("latency_ms") or 0,
                        prompt_tokens=doc.get("prompt_tokens"),
                        completion_tokens=doc.get("completion_tokens"),
                        total_tokens=doc.get("total_tokens"),
                        cost_usd=doc.get("cost_usd"),
                    )
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
            fallback_evidence=fallback_evidence,
            repeat_observation=repeat_observation,
        )
