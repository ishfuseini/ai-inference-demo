import json
from datetime import UTC, datetime

from openrouter_demo.models import (
    UNAVAILABLE,
    AttemptRecord,
    FallbackEvidence,
    InferenceRun,
    Status,
    TelemetryEvidence,
)
from openrouter_demo.routing import DEFAULT_STRATEGY
from openrouter_demo.sqlite_store import SQLiteRunHistory


def test_round_trip_preserves_sentinels_cache_trace_and_fallback(tmp_path) -> None:
    store = SQLiteRunHistory(db_path=str(tmp_path / "runs.db"))
    primary = AttemptRecord(
        model="nonexistent/fake-model-for-demo",
        provider=UNAVAILABLE,
        status=Status.FAILED,
        error_message="OpenRouter request failed (404)",
        latency_ms=12,
        prompt_tokens=UNAVAILABLE,
        completion_tokens=UNAVAILABLE,
        total_tokens=UNAVAILABLE,
        cost_usd=UNAVAILABLE,
    )
    fallback = AttemptRecord(
        model="openai/gpt-4o-mini",
        provider="OpenAI",
        status=Status.SUCCEEDED,
        error_message=None,
        latency_ms=200,
        prompt_tokens=3,
        completion_tokens=4,
        total_tokens=7,
        cost_usd=0.001,
    )
    run = InferenceRun(
        run_id="run-1",
        prompt="Prompt",
        strategy_name=DEFAULT_STRATEGY.name,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        status=Status.FALLBACK_SUCCEEDED,
        streamed_text="done",
        error_message=None,
        telemetry=TelemetryEvidence(
            model=UNAVAILABLE,
            provider="OpenAI",
            latency_ms=12,
            prompt_tokens=UNAVAILABLE,
            completion_tokens=UNAVAILABLE,
            total_tokens=UNAVAILABLE,
            cost_usd=UNAVAILABLE,
            cache_status="hit",
            cached_tokens=10,
            cache_write_tokens=0,
            trace_status="disabled",
            trace_id=None,
            trace_url=None,
        ),
        fallback_evidence=FallbackEvidence(primary=primary, fallback=fallback, simulated=True),
    )
    store.append(run)

    reloaded = store.get("run-1")
    assert reloaded is not None
    assert reloaded.telemetry is not None
    assert reloaded.telemetry.model is UNAVAILABLE
    assert not isinstance(reloaded.telemetry.model, dict)
    assert reloaded.telemetry.cached_tokens == 10
    assert reloaded.telemetry.trace_status == "disabled"
    assert reloaded.telemetry.cost_usd is UNAVAILABLE
    assert reloaded.fallback_evidence is not None
    assert reloaded.fallback_evidence.primary.status is Status.FAILED


def test_round_trip_preserves_unavailable_cache_status(tmp_path) -> None:
    store = SQLiteRunHistory(db_path=str(tmp_path / "runs.db"))
    run = InferenceRun(
        run_id="run-2",
        prompt="Prompt",
        strategy_name=DEFAULT_STRATEGY.name,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        status=Status.SUCCEEDED,
        streamed_text="done",
        error_message=None,
        telemetry=TelemetryEvidence(
            model="openai/gpt-4o-mini",
            provider="OpenAI",
            latency_ms=100,
            prompt_tokens=3,
            completion_tokens=4,
            total_tokens=7,
            cost_usd=0.001,
            cache_status=UNAVAILABLE,
            cached_tokens=UNAVAILABLE,
            cache_write_tokens=UNAVAILABLE,
        ),
    )
    store.append(run)

    reloaded = store.get("run-2")
    assert reloaded is not None
    assert reloaded.telemetry is not None
    assert reloaded.telemetry.cache_status is UNAVAILABLE
    assert not isinstance(reloaded.telemetry.cache_status, dict)


def test_legacy_flat_row_loads_via_compatibility_branch(tmp_path) -> None:
    store = SQLiteRunHistory(db_path=str(tmp_path / "runs.db"))
    legacy = json.dumps(
        {
            "model": "openai/gpt-4o-mini",
            "provider": "OpenAI",
            "latency_ms": 12,
            "prompt_tokens": 3,
            "completion_tokens": 4,
            "total_tokens": 7,
            "cost_usd": 0.001,
        }
    )
    with store._lock:
        cur = store._conn.cursor()
        cur.execute(
            "INSERT INTO runs (run_id, prompt, strategy_name, started_at, completed_at, status, streamed_text, error_message, telemetry_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "legacy-1",
                "Prompt",
                "default",
                "2026-08-19T00:00:00+00:00",
                "2026-08-19T00:00:01+00:00",
                "succeeded",
                "done",
                None,
                legacy,
            ),
        )
        store._conn.commit()

    reloaded = store.get("legacy-1")
    assert reloaded is not None
    assert reloaded.telemetry is not None
    assert reloaded.telemetry.model == "openai/gpt-4o-mini"
    assert reloaded.telemetry.latency_ms == 12
    assert reloaded.fallback_evidence is None
    assert reloaded.repeat_observation is None
