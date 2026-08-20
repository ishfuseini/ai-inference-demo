import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from openrouter_demo.client import _extract_cache
from openrouter_demo.config import (
    LANGFUSE_BASE_URL,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
    load_config,
)
from openrouter_demo.history import RunHistory
from openrouter_demo.models import (
    UNAVAILABLE,
    InferenceRun,
    Status,
    StreamChunk,
    StreamedResult,
    TelemetryEvidence,
    Unavailable,
)
from openrouter_demo.routing import DEFAULT_STRATEGY
from openrouter_demo.telemetry import TraceOutcome, record_trace
from openrouter_demo.ui import _run_inference, _telemetry_rows


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


def test_record_trace_disabled_without_credentials() -> None:
    outcome = record_trace(
        load_config({}),
        name="n",
        model="m",
        input={},
        output="o",
        usage_details={},
    )
    assert outcome == TraceOutcome(status="disabled", trace_id=None, trace_url=None)


def test_record_trace_failed_with_unreachable_langfuse(monkeypatch) -> None:
    monkeypatch.setenv(LANGFUSE_PUBLIC_KEY, "pk-lf-1234567890")
    monkeypatch.setenv(LANGFUSE_SECRET_KEY, "sk-lf-1234567890")
    monkeypatch.setenv(LANGFUSE_BASE_URL, "http://127.0.0.1:1")
    outcome = record_trace(
        load_config(),
        name="n",
        model="m",
        input={},
        output="o",
        usage_details={},
    )
    assert outcome.status == "failed"
    assert outcome.trace_id is None
    assert outcome.trace_url is None


def test_run_inference_trace_input_contains_no_api_key(monkeypatch) -> None:
    captured: dict = {}

    async def fake_stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        yield StreamChunk("hi")
        yield StreamedResult(
            text="hi",
            model="openai/gpt-4o-mini",
            provider="OpenAI",
            prompt_tokens=3,
            completion_tokens=4,
            total_tokens=7,
            cost_usd=0.001,
            latency_ms=10,
        )

    def fake_record_trace(config, *, name, model, input, output, usage_details):
        captured["input"] = input
        return TraceOutcome(status="disabled", trace_id=None, trace_url=None)

    monkeypatch.setattr("openrouter_demo.ui.record_trace", fake_record_trace)

    run = asyncio.run(
        _run_inference(
            "Prompt",
            api_key="sk-test",
            history=RunHistory(),
            stream_fn=fake_stream,
            config=load_config({}),
        )
    )

    assert run.status is Status.SUCCEEDED
    assert captured["input"] == {"prompt": "Prompt"}
    assert "api_key" not in captured["input"]
    assert "OPENROUTER_API_KEY" not in captured["input"]
