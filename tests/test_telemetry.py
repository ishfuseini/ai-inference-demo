from datetime import UTC, datetime

from openrouter_demo.client import _extract_cache
from openrouter_demo.models import (
    UNAVAILABLE,
    InferenceRun,
    Status,
    TelemetryEvidence,
    Unavailable,
)
from openrouter_demo.routing import DEFAULT_STRATEGY
from openrouter_demo.ui import _telemetry_rows


def test_telemetry_evidence_defaults_cache_and_trace_fields() -> None:
    telemetry = TelemetryEvidence(
        model="m",
        provider="p",
        latency_ms=1,
        prompt_tokens=UNAVAILABLE,
        completion_tokens=UNAVAILABLE,
        total_tokens=UNAVAILABLE,
        cost_usd=UNAVAILABLE,
    )
    assert telemetry.cache_status is UNAVAILABLE
    assert telemetry.cached_tokens is UNAVAILABLE
    assert telemetry.cache_write_tokens is UNAVAILABLE
    assert telemetry.trace_status is UNAVAILABLE
    assert telemetry.trace_id is None
    assert telemetry.trace_url is None
    assert telemetry.openrouter_metadata is UNAVAILABLE


def test_telemetry_evidence_round_trip_preserves_sentinels() -> None:
    telemetry = TelemetryEvidence(
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
        trace_status="enabled",
        trace_id="abc123",
        trace_url="https://cloud.langfuse.com/traces/abc123",
        openrouter_metadata={"id": "router-1"},
    )
    reloaded = TelemetryEvidence.from_dict(telemetry.to_dict())
    assert reloaded.model is UNAVAILABLE
    assert not isinstance(reloaded.model, dict)
    assert reloaded.provider == "OpenAI"
    assert reloaded.cache_status == "hit"
    assert reloaded.cached_tokens == 10
    assert reloaded.cache_write_tokens == 0
    assert reloaded.trace_status == "enabled"
    assert reloaded.trace_id == "abc123"
    assert reloaded.trace_url == "https://cloud.langfuse.com/traces/abc123"
    assert reloaded.openrouter_metadata == {"id": "router-1"}


def test_extract_cache_hit_write_and_absent() -> None:
    assert _extract_cache({"prompt_tokens_details": {"cached_tokens": 5, "cache_write_tokens": 0}}) == (
        "hit",
        5,
        0,
    )
    assert _extract_cache({"prompt_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 7}}) == (
        "write",
        0,
        7,
    )
    assert _extract_cache({}) == (UNAVAILABLE, UNAVAILABLE, UNAVAILABLE)
    assert _extract_cache({"prompt_tokens_details": "not-a-dict"}) == (
        UNAVAILABLE,
        UNAVAILABLE,
        UNAVAILABLE,
    )
    assert _extract_cache({"prompt_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0}}) == (
        UNAVAILABLE,
        UNAVAILABLE,
        UNAVAILABLE,
    )


def test_telemetry_rows_include_cache_and_trace() -> None:
    run = InferenceRun(
        run_id="run-cache-trace",
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
            latency_ms=200,
            prompt_tokens=3,
            completion_tokens=4,
            total_tokens=7,
            cost_usd=0.001,
            cache_status="hit",
            cached_tokens=10,
            cache_write_tokens=0,
            trace_status="enabled",
            trace_id="abc123",
            trace_url="https://cloud.langfuse.com/traces/abc123",
        ),
    )
    rows = dict(_telemetry_rows(run))
    assert "Cache" in rows
    assert "Trace" in rows
    assert rows["Cache"] == "Cache hit (10 tokens)"
    assert rows["Trace"] == "https://cloud.langfuse.com/traces/abc123"


def test_unavailable_sentinel_is_not_zero_or_dict() -> None:
    assert isinstance(UNAVAILABLE, Unavailable)
    assert not UNAVAILABLE
    assert UNAVAILABLE != 0
