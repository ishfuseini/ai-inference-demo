from dataclasses import dataclass
from typing import Literal

StrategyName = Literal["default", "cost", "intelligence"]

ROUTING_STRATEGY_LABELS: dict[StrategyName, str] = {
    "cost": "Cost",
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

INTELLIGENCE_STRATEGY = RoutingStrategy(
    name="intelligence",
    description="Prefer stronger models for quality-sensitive responses.",
    model="anthropic/claude-opus-5",
    provider_preferences=None,
)

STRATEGIES: dict[StrategyName, RoutingStrategy] = {
    "cost": COST_STRATEGY,
    "intelligence": INTELLIGENCE_STRATEGY,
}


def strategy_payload(strategy: RoutingStrategy) -> dict[str, object]:
    payload: dict[str, object] = {"model": strategy.model}
    if strategy.provider_preferences is not None:
        payload["provider"] = strategy.provider_preferences
    return payload
