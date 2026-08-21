from dataclasses import dataclass
from typing import Literal

StrategyName = Literal["default", "cost", "latency", "intelligence", "custom"]

ROUTING_STRATEGY_LABELS: dict[StrategyName, str] = {
    "cost": "Cost",
    "latency": "Latency",
    "intelligence": "Intelligence",
}


@dataclass(frozen=True)
class RoutingStrategy:
    name: StrategyName
    description: str
    model: str
    provider_preferences: dict[str, object] | None


DEFAULT_STRATEGY = RoutingStrategy(
    name="default",
    description="Balanced route for general quality and availability.",
    model="openai/gpt-4o-mini",
    provider_preferences=None,
)

COST_STRATEGY = RoutingStrategy(
    name="cost",
    description="Prefer lower-cost model/provider choices. Validate quality before adopting.",
    model="openai/gpt-4o-mini",
    provider_preferences={"sort": "price"},
)

LATENCY_STRATEGY = RoutingStrategy(
    name="latency",
    description="Prefer faster routes for interactive use cases.",
    model="openai/gpt-4o-mini",
    provider_preferences={"sort": "latency"},
)

INTELLIGENCE_STRATEGY = RoutingStrategy(
    name="intelligence",
    description="Prefer stronger models for quality-sensitive responses.",
    model="anthropic/claude-opus-5",
    provider_preferences=None,
)

FALLBACK_PRIMARY_STRATEGY = RoutingStrategy(
    name="custom",
    description="Simulated primary route failure for demo fallback scenario.",
    model="nonexistent/fake-model-for-demo",
    provider_preferences={"allow_fallbacks": False},
)

STRATEGIES: dict[StrategyName, RoutingStrategy] = {
    "cost": COST_STRATEGY,
    "latency": LATENCY_STRATEGY,
    "intelligence": INTELLIGENCE_STRATEGY,
}


def strategy_payload(strategy: RoutingStrategy) -> dict[str, object]:
    payload: dict[str, object] = {"model": strategy.model}
    if strategy.provider_preferences is not None:
        payload["provider"] = strategy.provider_preferences
    return payload
