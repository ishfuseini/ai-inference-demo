import base64
import json
import os
import urllib.parse
from dataclasses import dataclass

import httpx

from openrouter_demo.config import (
    LANGFUSE_BASE_URL,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
    AppConfig,
)
from openrouter_demo.models import LangfuseScore


@dataclass(frozen=True)
class TraceOutcome:
    status: str  # "enabled" | "disabled" | "failed"
    trace_id: str | None
    trace_url: str | None
    observation_id: str | None = None


@dataclass(frozen=True)
class FetchOutcome:
    status: str  # "enabled" | "disabled" | "failed"
    scores: tuple[LangfuseScore, ...] | None


@dataclass(frozen=True)
class ObservationDetails:
    model_name: str | None
    model_parameters: dict | None
    latency_ms: float | None


def record_trace(
    config: AppConfig,
    *,
    name: str,
    model: str,
    input: dict,
    output: str,
    usage_details: dict[str, int],
) -> TraceOutcome:
    if not config.langfuse_ready:
        return TraceOutcome(status="disabled", trace_id=None, trace_url=None)
    try:
        from langfuse import get_client

        client = get_client()
        with client.start_as_current_observation(
            name=name,
            as_type="generation",
            model=model,
            input=input,
            output=output,
            usage_details=usage_details,
        ) as gen:
            trace_id = gen.trace_id
            observation_id = gen.id
        client.flush()
        return TraceOutcome(
            status="enabled",
            trace_id=trace_id,
            trace_url=client.get_trace_url(trace_id=trace_id),
            observation_id=observation_id,
        )
    except Exception:  # noqa: BLE001 — tracing must never block or break inference
        return TraceOutcome(status="failed", trace_id=None, trace_url=None)


def _subject_ids(subject: dict | None) -> tuple[str | None, str | None]:
    """Extract (trace_id, observation_id) from a v3 score `subject` object."""
    if not subject:
        return None, None
    kind = subject.get("kind")
    if kind == "trace":
        return subject.get("id"), None
    if kind == "observation":
        return subject.get("traceId"), subject.get("id")
    return None, None


async def fetch_langfuse_scores(
    config: AppConfig,
    *,
    limit: int = 50,
    trace_id: str | None = None,
    observation_id: str | None = None,
) -> FetchOutcome:
    """Fetch individual Langfuse eval scores via the v3 Scores API.

    When `observation_id` (and its parent `trace_id`) are provided, the request
    is scoped to that observation — the entity eval scores are attached to.
    Returns FetchOutcome(status="disabled") when Langfuse is not configured,
    "enabled" with scores on success, or "failed" on any error — never blocks.
    """
    if not config.langfuse_ready:
        return FetchOutcome(status="disabled", scores=None)

    public_key = os.environ.get(LANGFUSE_PUBLIC_KEY, "")
    secret_key = os.environ.get(LANGFUSE_SECRET_KEY, "")
    base_url = os.environ.get(LANGFUSE_BASE_URL, "").rstrip("/")
    auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    params = [f"limit={limit}", "fields=details,subject"]
    if trace_id:
        params.append(f"traceId={trace_id}")
    if observation_id:
        params.append(f"observationId={observation_id}")
    url = f"{base_url}/api/public/v3/scores?{'&'.join(params)}"
    headers = {"Authorization": f"Basic {auth}"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            items = resp.json().get("data", [])
    except Exception:  # noqa: BLE001 — fetching must never block inference
        return FetchOutcome(status="failed", scores=())

    scores: list[LangfuseScore] = []
    for item in items:
        subject = item.get("subject")
        score_trace_id, score_observation_id = _subject_ids(subject)
        scores.append(
            LangfuseScore(
                id=item.get("id", ""),
                name=item.get("name", ""),
                value=item.get("value"),
                data_type=item.get("dataType", ""),
                source=item.get("source", ""),
                timestamp=item.get("timestamp", ""),
                trace_id=score_trace_id,
                observation_id=score_observation_id,
                comment=item.get("comment"),
            )
        )
    return FetchOutcome(status="enabled", scores=tuple(scores))


async def fetch_observation_details(
    config: AppConfig, *, observation_id: str
) -> ObservationDetails | None:
    """Fetch model name, parameters, and latency for a single observation.

    Returns None on any error — enrichment must never block the scores table.
    """
    if not config.langfuse_ready or not observation_id:
        return None

    public_key = os.environ.get(LANGFUSE_PUBLIC_KEY, "")
    secret_key = os.environ.get(LANGFUSE_SECRET_KEY, "")
    base_url = os.environ.get(LANGFUSE_BASE_URL, "").rstrip("/")
    auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    filter_json = json.dumps(
        [{"type": "string", "column": "id", "operator": "=", "value": observation_id}]
    )
    url = (
        f"{base_url}/api/public/v2/observations?fields=model,metrics"
        f"&filter={urllib.parse.quote(filter_json)}"
    )
    headers = {"Authorization": f"Basic {auth}"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            items = resp.json().get("data", [])
    except Exception:  # noqa: BLE001 — enrichment must never block the table
        return None

    if not items:
        return None
    item = items[0]
    return ObservationDetails(
        model_name=item.get("model"),
        model_parameters=item.get("modelParameters"),
        latency_ms=item.get("latency"),
    )
