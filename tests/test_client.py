import asyncio
import json

import httpx
import pytest

from openrouter_demo.client import (
    OpenRouterAuthError,
    OpenRouterHTTPError,
    stream_chat_completion,
)
from openrouter_demo.models import UNAVAILABLE, StreamChunk, StreamedResult, Unavailable
from openrouter_demo.routing import DEFAULT_STRATEGY


def _sse_bytes(chunks: list[dict]) -> bytes:
    lines: list[str] = []
    for c in chunks:
        lines.append(f"data: {json.dumps(c)}")
        lines.append("")
    lines.append("data: [DONE]")
    lines.append("")
    return "\n".join(lines).encode()


def _client_with(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def test_stream_concatenates_deltas_and_returns_result() -> None:
    chunks = [
        {"choices": [{"delta": {"content": "Hello"}}], "model": "openai/gpt-4o-mini"},
        {"choices": [{"delta": {"content": " world"}}]},
        {
            "choices": [{"delta": {"content": "!"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8, "cost": 0.001},
            "provider": "openai",
        },
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("authorization") == "Bearer test-key"
        body = json.loads(request.content)
        assert body["model"] == "openai/gpt-4o-mini"
        assert body["stream"] is True
        return httpx.Response(200, content=_sse_bytes(chunks))

    async def _run() -> tuple[list[str], StreamedResult | None]:
        deltas: list[str] = []
        result: StreamedResult | None = None
        async for item in stream_chat_completion(
            "hi", strategy=DEFAULT_STRATEGY, api_key="test-key", http_client=_client_with(handler)
        ):
            if isinstance(item, StreamChunk):
                deltas.append(item.text_delta)
            elif isinstance(item, StreamedResult):
                result = item
        return deltas, result

    deltas, result = asyncio.run(_run())
    assert deltas == ["Hello", " world", "!"]
    assert result is not None
    assert result.text == "Hello world!"
    assert result.model == "openai/gpt-4o-mini"
    assert result.provider == "openai"
    assert result.prompt_tokens == 5
    assert result.cost_usd == 0.001


def test_stream_requires_strategy_or_model() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        pytest.fail("handler should not be invoked when validation fails")

    with pytest.raises(ValueError, match="Either strategy or model must be provided."):
        asyncio.run(
            stream_chat_completion(
                "hi", strategy=None, model=None, api_key="k", http_client=_client_with(handler)
            ).__anext__()
        )


def test_stream_plain_model_without_strategy() -> None:
    chunks = [
        {"choices": [{"delta": {"content": "hi"}}], "model": "openai/gpt-4o-mini"},
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content)["model"] == "openai/gpt-4o-mini"
        return httpx.Response(200, content=_sse_bytes(chunks))

    async def _run() -> StreamedResult | None:
        result: StreamedResult | None = None
        async for item in stream_chat_completion(
            "hi", model="openai/gpt-4o-mini", api_key="k", http_client=_client_with(handler)
        ):
            if isinstance(item, StreamedResult):
                result = item
        return result

    result = asyncio.run(_run())
    assert result is not None
    assert result.model == "openai/gpt-4o-mini"


def test_stream_provider_falls_back_to_openrouter_metadata() -> None:
    chunks = [
        {
            "choices": [{"delta": {"content": "hi"}}],
            "model": "openai/gpt-4o-mini",
            "openrouter_metadata": {"provider": "some-provider"},
        },
    ]

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_sse_bytes(chunks))

    async def _run() -> StreamedResult | None:
        result: StreamedResult | None = None
        async for item in stream_chat_completion(
            "hi", strategy=DEFAULT_STRATEGY, api_key="k", http_client=_client_with(handler)
        ):
            if isinstance(item, StreamedResult):
                result = item
        return result

    result = asyncio.run(_run())
    assert result is not None
    assert result.provider == "some-provider"


def test_stream_missing_usage_is_unavailable() -> None:
    chunks = [
        {"choices": [{"delta": {"content": "hi"}}], "model": "openai/gpt-4o-mini"},
    ]

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_sse_bytes(chunks))

    async def _run() -> StreamedResult | None:
        result: StreamedResult | None = None
        async for item in stream_chat_completion(
            "hi", strategy=DEFAULT_STRATEGY, api_key="k", http_client=_client_with(handler)
        ):
            if isinstance(item, StreamedResult):
                result = item
        return result

    result = asyncio.run(_run())
    assert result is not None
    assert result.prompt_tokens is UNAVAILABLE
    assert result.completion_tokens is UNAVAILABLE
    assert result.total_tokens is UNAVAILABLE
    assert result.cost_usd is UNAVAILABLE
    assert isinstance(result.prompt_tokens, Unavailable)
    assert result.prompt_tokens != 0


def test_stream_401_raises_auth_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, content=b"unauthorized")

    async def _run() -> None:
        async for _ in stream_chat_completion(
            "hi", strategy=DEFAULT_STRATEGY, api_key="bad", http_client=_client_with(handler)
        ):
            pass

    with pytest.raises(OpenRouterAuthError):
        asyncio.run(_run())


def test_stream_sends_metadata_header_and_extracts_cache_hit() -> None:
    chunks = [
        {
            "choices": [{"delta": {"content": "cached"}}],
            "model": "openai/gpt-4o-mini",
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 5,
                "total_tokens": 105,
                "cost": 0.002,
                "prompt_tokens_details": {"cached_tokens": 90, "cache_write_tokens": 0},
            },
        },
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("x-openrouter-metadata") == "enabled"
        return httpx.Response(200, content=_sse_bytes(chunks))

    async def _run() -> StreamedResult | None:
        result: StreamedResult | None = None
        async for item in stream_chat_completion(
            "hi", strategy=DEFAULT_STRATEGY, api_key="k", http_client=_client_with(handler)
        ):
            if isinstance(item, StreamedResult):
                result = item
        return result

    result = asyncio.run(_run())
    assert result is not None
    assert result.cache_status == "hit"
    assert result.cached_tokens == 90
    assert result.cache_write_tokens == 0


def test_stream_missing_cache_details_is_unavailable() -> None:
    chunks = [
        {
            "choices": [{"delta": {"content": "hi"}}],
            "model": "openai/gpt-4o-mini",
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 3,
                "total_tokens": 8,
                "cost": 0.001,
            },
        },
    ]

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_sse_bytes(chunks))

    async def _run() -> StreamedResult | None:
        result: StreamedResult | None = None
        async for item in stream_chat_completion(
            "hi", strategy=DEFAULT_STRATEGY, api_key="k", http_client=_client_with(handler)
        ):
            if isinstance(item, StreamedResult):
                result = item
        return result

    result = asyncio.run(_run())
    assert result is not None
    assert result.cache_status is UNAVAILABLE
    assert result.cached_tokens is UNAVAILABLE
    assert result.cache_write_tokens is UNAVAILABLE
    assert result.openrouter_metadata is UNAVAILABLE


def test_stream_preserves_partial_text_on_error_payload() -> None:
    chunks = [
        {"choices": [{"delta": {"content": "partial"}}]},
        {"error": {"message": "provider unavailable"}},
    ]

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_sse_bytes(chunks))

    async def _run() -> None:
        async for item in stream_chat_completion(
            "hi", strategy=DEFAULT_STRATEGY, api_key="k", http_client=_client_with(handler)
        ):
            if isinstance(item, StreamChunk):
                pass

    with pytest.raises(OpenRouterHTTPError) as exc:
        asyncio.run(_run())
    assert exc.value.partial_text == "partial"
