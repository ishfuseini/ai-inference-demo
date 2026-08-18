from typing import Literal

StrategyName = Literal["default", "cost", "latency", "custom"]

ROUTING_STRATEGY_LABELS: dict[StrategyName, str] = {
    "default": "Default",
    "cost": "Cost optimized",
    "latency": "Latency optimized",
    "custom": "Custom",
}
