from __future__ import annotations

from collections.abc import AsyncIterator, Callable

from openrouter_demo.models import StreamChunk, StreamedResult

type StreamFn = Callable[..., AsyncIterator[StreamChunk | StreamedResult]]
