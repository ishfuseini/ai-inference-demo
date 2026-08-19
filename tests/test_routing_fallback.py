import pytest

from src.routing.router import Router, RoutingStrategy


class DummyError(Exception):
    pass


def success_call(provider, **kwargs):
    return f"ok:{provider}"


def fail_call(provider, **kwargs):
    raise DummyError(f"failed:{provider}")


def test_round_robin_and_fallback_success():
    r = Router(["a", "b", "c"])
    # first call should pick 'a' for priority default, but test round robin
    res = r.call_with_fallback(RoutingStrategy.ROUND_ROBIN, success_call)
    assert res["result"].startswith("ok:")


def test_fallback_path_on_failure():
    r = Router(["a", "b"])

    def call_fn(provider, **kwargs):
        if provider == "a":
            raise DummyError("fail a")
        return "ok:b"

    res = r.call_with_fallback(RoutingStrategy.PRIORITY, call_fn)
    assert res["provider"] == "b"
    assert res["attempted"] == ["a", "b"]
