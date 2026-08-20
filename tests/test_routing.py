from openrouter_demo.models import UNAVAILABLE, AttemptRecord, FallbackEvidence, Status
from openrouter_demo.routing import (
    COST_STRATEGY,
    DEFAULT_STRATEGY,
    FALLBACK_PRIMARY_STRATEGY,
    LATENCY_STRATEGY,
    STRATEGIES,
    strategy_payload,
)


def test_default_strategy_payload_has_no_provider() -> None:
    payload = strategy_payload(DEFAULT_STRATEGY)
    assert payload == {"model": "openai/gpt-4o-mini"}
    assert "provider" not in payload


def test_cost_strategy_payload_includes_price_sort() -> None:
    payload = strategy_payload(COST_STRATEGY)
    assert payload["model"] == "openai/gpt-4o-mini"
    assert payload["provider"] == {"sort": "price"}


def test_latency_strategy_payload_includes_latency_sort() -> None:
    payload = strategy_payload(LATENCY_STRATEGY)
    assert payload["model"] == "openai/gpt-4o-mini"
    assert payload["provider"] == {"sort": "latency"}


def test_fallback_primary_strategy_payload_includes_allow_fallbacks_false() -> None:
    payload = strategy_payload(FALLBACK_PRIMARY_STRATEGY)
    assert payload["model"] == "nonexistent/fake-model-for-demo"
    assert payload["provider"] == {"allow_fallbacks": False}


def test_strategies_dict_contains_three_selectable_strategies() -> None:
    assert set(STRATEGIES.keys()) == {"default", "cost", "latency"}
    assert STRATEGIES["default"] is DEFAULT_STRATEGY
    assert STRATEGIES["cost"] is COST_STRATEGY
    assert STRATEGIES["latency"] is LATENCY_STRATEGY


def test_status_fallback_succeeded_value() -> None:
    assert Status.FALLBACK_SUCCEEDED == "fallback_succeeded"


def test_attempt_record_is_frozen_dataclass() -> None:
    record = AttemptRecord(
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
    assert record.model == "nonexistent/fake-model-for-demo"
    assert record.provider is UNAVAILABLE
    assert record.status is Status.FAILED
    assert record.error_message == "OpenRouter request failed (404)"
    assert record.latency_ms == 12

    # Frozen — mutation must fail
    try:
        record.model = "other"
    except AttributeError:
        pass
    else:  # pragma: no cover
        raise AssertionError("AttemptRecord must be frozen")


def test_fallback_evidence_is_frozen_dataclass() -> None:
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
    evidence = FallbackEvidence(primary=primary, fallback=fallback, simulated=True)
    assert evidence.primary is primary
    assert evidence.fallback is fallback
    assert evidence.simulated is True

    try:
        evidence.simulated = False
    except AttributeError:
        pass
    else:  # pragma: no cover
        raise AssertionError("FallbackEvidence must be frozen")