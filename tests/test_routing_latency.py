from src.routing.router import Router, RoutingStrategy
from routing.telemetry import record_latency


def test_latency_strategy_prefers_low_latency():
    r = Router(["fast", "slow"]) 
    # record latencies so avg(fast) < avg(slow)
    record_latency("fast", 50.0)
    record_latency("fast", 30.0)
    record_latency("slow", 200.0)
    record_latency("slow", 180.0)

    selected = r.select_provider(RoutingStrategy.LATENCY)
    assert selected == "fast"


def test_latency_strategy_partial_and_missing_data():
    # case: only one provider has latency data
    r = Router(["a", "b", "c"])
    record_latency("b", 100.0)

    selected = r.select_provider(RoutingStrategy.LATENCY)
    assert selected == "b"

    # case: no latency data -> fallback to priority (index 0)
    r2 = Router(["x", "y"])
    selected2 = r2.select_provider(RoutingStrategy.LATENCY)
    assert selected2 == "x"
