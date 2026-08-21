from openrouter_demo.models import Status
from openrouter_demo.routing import (
    COST_STRATEGY,
    DEFAULT_STRATEGY,
    INTELLIGENCE_STRATEGY,
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


def test_intelligence_strategy_payload_has_no_provider_sort() -> None:
    payload = strategy_payload(INTELLIGENCE_STRATEGY)
    assert payload == {"model": "anthropic/claude-opus-5"}


def test_strategies_dict_contains_two_selectable_strategies() -> None:
    assert set(STRATEGIES.keys()) == {"cost", "intelligence"}
    assert STRATEGIES["cost"] is COST_STRATEGY
    assert STRATEGIES["intelligence"] is INTELLIGENCE_STRATEGY


def test_status_fallback_succeeded_value() -> None:
    assert Status.FALLBACK_SUCCEEDED == "fallback_succeeded"


