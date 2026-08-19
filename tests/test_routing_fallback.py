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

    # perform several calls and assert round-robin provider selection
    results = []
    attempted_sequences = []

    for _ in range(5):
        res = r.call_with_fallback(RoutingStrategy.ROUND_ROBIN, success_call)
        results.append(res["result"])
        attempted_sequences.append(res["attempted"])

    # providers should be selected in round-robin order over successive calls
    providers = [result.split("ok:")[1] for result in results]
    assert providers == ["a", "b", "c", "a", "b"]

    # on a successful call only the chosen provider should be attempted
    for provider, attempted in zip(providers, attempted_sequences):
        assert attempted == [provider]


def test_fallback_path_on_failure():
    r = Router(["a", "b"])

    def call_fn(provider, **kwargs):
        if provider == "a":
            raise DummyError("fail a")
        return "ok:b"

    res = r.call_with_fallback(RoutingStrategy.PRIORITY, call_fn)
    assert res["provider"] == "b"
    assert res["attempted"] == ["a", "b"]


def test_all_providers_fail_raises():
    r = Router(["a", "b"])

    with pytest.raises(DummyError) as excinfo:
        r.call_with_fallback(RoutingStrategy.PRIORITY, fail_call)

    # ensure the raised exception is the one from the last provider attempted
    assert "failed:b" in str(excinfo.value)
