import asyncio
from collections.abc import AsyncIterator

import httpx

from openrouter_demo.client import _extract_cache
from openrouter_demo.config import (
    LANGFUSE_BASE_URL,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
    load_config,
)
from openrouter_demo.models import (
    UNAVAILABLE,
    LangfuseScore,
    Status,
    StreamChunk,
    StreamedResult,
    TelemetryEvidence,
    Unavailable,
)
from openrouter_demo.sqlite_store import SQLiteRunHistory
from openrouter_demo.telemetry import (
    FetchOutcome,
    TraceOutcome,
    fetch_langfuse_scores,
    record_trace,
)
from openrouter_demo.ui import _run_inference


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
    assert _extract_cache(
        {"prompt_tokens_details": {"cached_tokens": 5, "cache_write_tokens": 0}}
    ) == (
        "hit",
        5,
        0,
    )
    assert _extract_cache(
        {"prompt_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 7}}
    ) == (
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
    assert _extract_cache(
        {"prompt_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0}}
    ) == (
        UNAVAILABLE,
        UNAVAILABLE,
        UNAVAILABLE,
    )


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
            history=SQLiteRunHistory(db_path=":memory:"),
            stream_fn=fake_stream,
            config=load_config({}),
        )
    )

    assert run.status is Status.SUCCEEDED
    assert captured["input"] == {"prompt": "Prompt"}
    assert "api_key" not in captured["input"]
    assert "OPENROUTER_API_KEY" not in captured["input"]


def _set_langfuse_env(monkeypatch) -> None:
    monkeypatch.setenv(LANGFUSE_PUBLIC_KEY, "pk-lf-test")
    monkeypatch.setenv(LANGFUSE_SECRET_KEY, "sk-lf-test")
    monkeypatch.setenv(LANGFUSE_BASE_URL, "https://cloud.langfuse.com")


def _v3_response() -> dict:
    return {
        "data": [
            {
                "id": "score-1",
                "name": "auto_fail",
                "value": 0,
                "dataType": "BOOLEAN",
                "source": "EVAL",
                "timestamp": "2026-08-21T04:22:40Z",
                "comment": "No auto-fail triggered.",
                "subject": {
                    "kind": "observation",
                    "id": "obs-1",
                    "traceId": "trace-1",
                },
            },
            {
                "id": "score-2",
                "name": "tone",
                "value": 5,
                "dataType": "NUMERIC",
                "source": "EVAL",
                "timestamp": "2026-08-21T04:22:41Z",
                "comment": None,
                "subject": {"kind": "trace", "id": "trace-2"},
            },
            {
                "id": "score-3",
                "name": "category",
                "value": "empathy",
                "dataType": "CATEGORICAL",
                "source": "API",
                "timestamp": "2026-08-21T04:22:42Z",
                "comment": None,
                "subject": None,
            },
        ],
        "meta": {"limit": 50},
    }


def test_langfuse_score_display_value_per_data_type() -> None:
    assert (
        LangfuseScore(
            id="b", name="n", value=0, data_type="BOOLEAN", source="EVAL", timestamp="t"
        ).display_value
        == "False"
    )
    assert (
        LangfuseScore(
            id="b", name="n", value=1, data_type="BOOLEAN", source="EVAL", timestamp="t"
        ).display_value
        == "True"
    )
    assert (
        LangfuseScore(
            id="n", name="n", value=5, data_type="NUMERIC", source="EVAL", timestamp="t"
        ).display_value
        == "5"
    )
    assert (
        LangfuseScore(
            id="c",
            name="n",
            value="empathy",
            data_type="CATEGORICAL",
            source="API",
            timestamp="t",
        ).display_value
        == "empathy"
    )


def test_langfuse_score_round_trip_preserves_fields() -> None:
    score = LangfuseScore(
        id="score-1",
        name="auto_fail",
        value=0,
        data_type="BOOLEAN",
        source="EVAL",
        timestamp="2026-08-21T04:22:40Z",
        trace_id="trace-1",
        observation_id="obs-1",
        comment="No auto-fail triggered.",
    )
    reloaded = LangfuseScore.from_dict(score.to_dict())
    assert reloaded == score
    assert reloaded.display_value == "False"


def test_fetch_scores_disabled_when_langfuse_not_configured(monkeypatch) -> None:
    monkeypatch.delenv(LANGFUSE_PUBLIC_KEY, raising=False)
    monkeypatch.delenv(LANGFUSE_SECRET_KEY, raising=False)
    monkeypatch.delenv(LANGFUSE_BASE_URL, raising=False)
    outcome = asyncio.run(fetch_langfuse_scores(load_config({})))
    assert outcome == FetchOutcome(status="disabled", scores=None)


def test_fetch_scores_enabled_with_mocked_v3_response(monkeypatch) -> None:
    _set_langfuse_env(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        assert "fields=details,subject" in str(request.url)
        assert request.headers["Authorization"].startswith("Basic ")
        return httpx.Response(200, json=_v3_response())

    real_async_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: real_async_client(transport=httpx.MockTransport(handler), **kw),
    )
    outcome = asyncio.run(fetch_langfuse_scores(load_config()))

    assert outcome.status == "enabled"
    assert outcome.scores is not None
    assert len(outcome.scores) == 3
    assert outcome.scores[0].id == "score-1"
    assert outcome.scores[0].trace_id == "trace-1"
    assert outcome.scores[0].observation_id == "obs-1"
    assert outcome.scores[0].comment == "No auto-fail triggered."
    assert outcome.scores[0].display_value == "False"
    assert outcome.scores[1].trace_id == "trace-2"
    assert outcome.scores[1].observation_id is None
    assert outcome.scores[2].trace_id is None


def test_fetch_scores_failed_on_http_error(monkeypatch) -> None:
    _set_langfuse_env(monkeypatch)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    real_async_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: real_async_client(transport=httpx.MockTransport(handler), **kw),
    )
    outcome = asyncio.run(fetch_langfuse_scores(load_config()))

    assert outcome.status == "failed"
    assert outcome.scores == ()


def test_fetch_scores_failed_on_connect_error(monkeypatch) -> None:
    monkeypatch.setenv(LANGFUSE_PUBLIC_KEY, "pk-lf-test")
    monkeypatch.setenv(LANGFUSE_SECRET_KEY, "sk-lf-test")
    monkeypatch.setenv(LANGFUSE_BASE_URL, "http://127.0.0.1:1")
    outcome = asyncio.run(fetch_langfuse_scores(load_config()))

    assert outcome.status == "failed"
    assert outcome.scores == ()
