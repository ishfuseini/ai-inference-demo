from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator

import httpx

from openrouter_demo.models import UNAVAILABLE, StreamChunk, StreamedResult, Unavailable
from openrouter_demo.routing import RoutingStrategy, strategy_payload

OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterError(Exception):
    def __init__(self, message: str, *, partial_text: str = "") -> None:
        super().__init__(message)
        self.partial_text = partial_text


class OpenRouterAuthError(OpenRouterError):
    pass


class OpenRouterHTTPError(OpenRouterError):
    def __init__(self, message: str, *, status_code: int, partial_text: str = "") -> None:
        super().__init__(message, partial_text=partial_text)
        self.status_code = status_code


class OpenRouterTimeoutError(OpenRouterError):
    pass


def _delta_content(payload: dict) -> str | None:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0]
    if not isinstance(first, dict):
        return None
    delta = first.get("delta")
    if not isinstance(delta, dict):
        return None
    content = delta.get("content")
    if isinstance(content, str) and content:
        return content
    return None


def _extract_provider(payload: dict) -> str | Unavailable:
    provider = payload.get("provider")
    if isinstance(provider, str) and provider:
        return provider
    meta = payload.get("openrouter_metadata")
    if isinstance(meta, dict):
        p2 = meta.get("provider")
        if isinstance(p2, str) and p2:
            return p2
    return UNAVAILABLE


def _extract_model(payload: dict) -> str | Unavailable:
    model = payload.get("model")
    if isinstance(model, str) and model:
        return model
    return UNAVAILABLE


def _extract_usage(payload: dict) -> tuple[int | Unavailable, int | Unavailable, int | Unavailable, float | Unavailable]:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return UNAVAILABLE, UNAVAILABLE, UNAVAILABLE, UNAVAILABLE
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    total_tokens = usage.get("total_tokens")
    cost = usage.get("cost")
    if cost is None:
        cost = usage.get("total_cost")
    pt: int | Unavailable = prompt_tokens if isinstance(prompt_tokens, int) else UNAVAILABLE
    ct: int | Unavailable = completion_tokens if isinstance(completion_tokens, int) else UNAVAILABLE
    tt: int | Unavailable = total_tokens if isinstance(total_tokens, int) else UNAVAILABLE
    co: float | Unavailable
    if isinstance(cost, (int, float)):
        co = float(cost)
    else:
        co = UNAVAILABLE
    return pt, ct, tt, co


async def stream_chat_completion(
    prompt: str,
    *,
    strategy: RoutingStrategy | None = None,
    model: str | None = None,
    api_key: str,
    http_client: httpx.AsyncClient | None = None,
    request_timeout: float = 60.0,
) -> AsyncIterator[StreamChunk | StreamedResult]:
    if strategy is None and model is None:
        raise ValueError("Either strategy or model must be provided.")
    resolved_model = model or (strategy.model if strategy is not None else None)
    assert resolved_model is not None

    if strategy is not None:
        body: dict[str, object] = {**strategy_payload(strategy), "messages": [{"role": "user", "content": prompt}], "stream": True}
        # strategy_payload already contains model; ensure consistency
        body["model"] = resolved_model
    else:
        body = {"model": resolved_model, "messages": [{"role": "user", "content": prompt}], "stream": True}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    start = time.monotonic()
    text_parts: list[str] = []
    seen_model: str | Unavailable = UNAVAILABLE
    seen_provider: str | Unavailable = UNAVAILABLE
    seen_pt: int | Unavailable = UNAVAILABLE
    seen_ct: int | Unavailable = UNAVAILABLE
    seen_tt: int | Unavailable = UNAVAILABLE
    seen_cost: float | Unavailable = UNAVAILABLE

    owns_client = http_client is None
    client = http_client if http_client is not None else httpx.AsyncClient(timeout=request_timeout)

    try:
        try:
            async with client.stream(
                "POST", OPENROUTER_CHAT_COMPLETIONS_URL, json=body, headers=headers, timeout=request_timeout
            ) as response:
                if response.status_code == 401:
                    partial = "".join(text_parts)
                    raise OpenRouterAuthError(
                        f"OpenRouter auth failed ({response.status_code})", partial_text=partial
                    )
                if response.status_code >= 400:
                    partial = "".join(text_parts)
                    raise OpenRouterHTTPError(
                        f"OpenRouter request failed ({response.status_code})",
                        status_code=response.status_code,
                        partial_text=partial,
                    )

                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        payload = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    if isinstance(payload, dict) and "error" in payload:
                        err = payload["error"]
                        msg = err.get("message") if isinstance(err, dict) else str(err)
                        partial = "".join(text_parts)
                        raise OpenRouterHTTPError(
                            str(msg) if msg else "OpenRouter error",
                            status_code=response.status_code,
                            partial_text=partial,
                        )

                    if not isinstance(payload, dict):
                        continue

                    # capture metadata when present
                    m = _extract_model(payload)
                    if not isinstance(m, Unavailable):
                        seen_model = m
                    p = _extract_provider(payload)
                    if not isinstance(p, Unavailable):
                        seen_provider = p
                    pt, ct, tt, co = _extract_usage(payload)
                    if not isinstance(pt, Unavailable):
                        seen_pt = pt
                    if not isinstance(ct, Unavailable):
                        seen_ct = ct
                    if not isinstance(tt, Unavailable):
                        seen_tt = tt
                    if not isinstance(co, Unavailable):
                        seen_cost = co

                    delta = _delta_content(payload)
                    if delta is not None:
                        text_parts.append(delta)
                        yield StreamChunk(text_delta=delta)

        except OpenRouterError:
            raise
        except httpx.TimeoutException as exc:
            partial = "".join(text_parts)
            raise OpenRouterTimeoutError(f"OpenRouter request timed out: {exc}", partial_text=partial) from exc
        except httpx.HTTPError as exc:
            partial = "".join(text_parts)
            # already handled status codes above; treat as generic HTTP error
            raise OpenRouterHTTPError(str(exc), status_code=0, partial_text=partial) from exc

        latency_ms = int((time.monotonic() - start) * 1000)
        full_text = "".join(text_parts)
        # if no model seen from stream, fall back to requested model
        final_model: str | Unavailable = seen_model if not isinstance(seen_model, Unavailable) else resolved_model
        yield StreamedResult(
            text=full_text,
            model=final_model,
            provider=seen_provider,
            prompt_tokens=seen_pt,
            completion_tokens=seen_ct,
            total_tokens=seen_tt,
            cost_usd=seen_cost,
            latency_ms=latency_ms,
        )
    finally:
        if owns_client:
            await client.aclose()
