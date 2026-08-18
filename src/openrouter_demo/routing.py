from dataclasses import dataclass
from typing import Literal

StrategyName = Literal["default", "cost", "latency", "custom"]

ROUTING_STRATEGY_LABELS: dict[StrategyName, str] = {
    "default": "Default",
    "cost": "Cost optimized",
    "latency": "Latency optimized",
    "custom": "Custom",
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


def strategy_payload(strategy: RoutingStrategy) -> dict[str, object]:
    return {"model": strategy.model}