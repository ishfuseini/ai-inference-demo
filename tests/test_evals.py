import asyncio
import json
from collections.abc import AsyncIterator

import pytest

import openrouter_demo.evals as evals_mod
from openrouter_demo.config import load_config
from openrouter_demo.evals import (
    EvalCase,
    EvalSummary,
    load_cases,
    main,
    run_eval_case,
    run_eval_set,
    score_response,
)
from openrouter_demo.models import UNAVAILABLE, StreamChunk, StreamedResult
from openrouter_demo.routing import COST_STRATEGY, DEFAULT_STRATEGY
from openrouter_demo.telemetry import TraceOutcome


def _case(case_id: str = "complaint-timeout-01") -> EvalCase:
    return EvalCase(
        case_id=case_id,
        name="Timeout during launch window",
        prompt="Your API timed out during our launch window.",
        expected_terms=("launch", "request id", "timestamp"),
        forbidden_terms=(),
    )


def _result(**overrides: object) -> StreamedResult:
    fields: dict[str, object] = {
        "text": "launch request id timestamp",
        "model": "openai/gpt-4o-mini",
        "provider": "OpenAI",
        "prompt_tokens": 3,
        "completion_tokens": 4,
        "total_tokens": 7,
        "cost_usd": 0.001,
        "latency_ms": 120,
    }
    fields.update(overrides)
    return StreamedResult(**fields)  # type: ignore[arg-type]


def _fake_stream(result: StreamedResult | None = None) -> object:
    async def stream(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        if result is not None:
            yield result

    return stream


def _run(coro: object) -> object:
    return asyncio.run(coro)


def test_score_response_passes_and_fails() -> None:
    case = EvalCase("c", "n", "p", ("launch", "timestamp"), ("never",), "")

    ok, reason, matched, missed, tripped = score_response(case, "we hit launch at timestamp")
    assert ok is True
    assert matched == ("launch", "timestamp")
    assert missed == ()
    assert tripped == ()

    ok2, _, _, missed2, tripped2 = score_response(case, "we hit launch")
    assert ok2 is False
    assert missed2 == ("timestamp",)
    assert tripped2 == ()

    ok3, _, _, _, tripped3 = score_response(case, "launch timestamp never again")
    assert ok3 is False
    assert tripped3 == ("never",)

    ok4, _, _, missed4, _ = score_response(case, "")
    assert ok4 is False
    assert missed4 == ("launch", "timestamp")


def test_load_cases_reads_three_to_five_cases() -> None:
    cases = load_cases()
    assert 3 <= len(cases) <= 5
    assert all(isinstance(case, EvalCase) for case in cases)
    assert cases[0].case_id == "complaint-timeout-01"


def test_load_cases_rejects_out_of_bounds(tmp_path) -> None:
    for count in (2, 6):
        path = tmp_path / "cases.json"
        path.write_text(
            json.dumps(
                {
                    "cases": [
                        {
                            "case_id": f"c{i}",
                            "name": "n",
                            "prompt": "p",
                            "expected_terms": [],
                            "forbidden_terms": [],
                        }
                        for i in range(count)
                    ]
                }
            )
        )
        with pytest.raises(ValueError):
            load_cases(str(path))


def test_run_eval_case_result_fields() -> None:
    result = _run(
        run_eval_case(
            _case(),
            strategy=DEFAULT_STRATEGY,
            api_key="sk-test",
            config=load_config({}),
            stream_fn=_fake_stream(_result()),
        )
    )
    assert isinstance(result, evals_mod.EvalResult)
    assert result.strategy_name == "default"
    assert result.passed is True
    assert "matched" in result.score_reason
    assert result.telemetry is not None
    assert result.telemetry.model == "openai/gpt-4o-mini"
    assert result.telemetry.provider == "OpenAI"
    assert result.telemetry.latency_ms == 120


def test_run_eval_case_preserves_unavailable() -> None:
    result = _run(
        run_eval_case(
            _case(),
            strategy=DEFAULT_STRATEGY,
            api_key="sk-test",
            config=load_config({}),
            stream_fn=_fake_stream(
                _result(
                    model=UNAVAILABLE,
                    provider=UNAVAILABLE,
                    prompt_tokens=UNAVAILABLE,
                    completion_tokens=UNAVAILABLE,
                    total_tokens=UNAVAILABLE,
                    cost_usd=UNAVAILABLE,
                )
            ),
        )
    )
    assert result.telemetry is not None
    assert result.telemetry.model is UNAVAILABLE
    assert result.telemetry.cost_usd is UNAVAILABLE


def test_run_eval_case_trace_disabled_and_enabled(monkeypatch) -> None:
    stream = _fake_stream(_result())
    disabled = _run(
        run_eval_case(
            _case(),
            strategy=DEFAULT_STRATEGY,
            api_key="sk-test",
            config=load_config({}),
            stream_fn=stream,
        )
    )
    assert disabled.telemetry.trace_status == "disabled"

    monkeypatch.setattr(
        evals_mod, "record_trace", lambda **kwargs: TraceOutcome("enabled", "tid", "url")
    )
    enabled = _run(
        run_eval_case(
            _case(),
            strategy=DEFAULT_STRATEGY,
            api_key="sk-test",
            config=load_config({}),
            stream_fn=stream,
        )
    )
    assert enabled.telemetry.trace_status == "enabled"
    assert enabled.telemetry.trace_id == "tid"


def test_run_eval_case_trace_input_has_no_api_key(monkeypatch) -> None:
    captured: dict = {}

    def fake_record_trace(**kwargs: object) -> TraceOutcome:
        captured.update(kwargs)
        return TraceOutcome("disabled", None, None)

    monkeypatch.setattr(evals_mod, "record_trace", fake_record_trace)
    case = _case()
    _run(
        run_eval_case(
            case,
            strategy=DEFAULT_STRATEGY,
            api_key="sk-test-secret",
            config=load_config({}),
            stream_fn=_fake_stream(_result()),
        )
    )
    assert captured["input"] == {"prompt": case.prompt}
    assert "sk-test-secret" not in str(captured)


def test_run_eval_set_compares_two_strategies(monkeypatch) -> None:
    monkeypatch.setattr(
        evals_mod, "record_trace", lambda **kwargs: TraceOutcome("disabled", None, None)
    )
    cases = [_case(f"c{i}") for i in range(3)]
    summary = _run(
        run_eval_set(
            cases,
            strategies=(DEFAULT_STRATEGY, COST_STRATEGY),
            api_key="sk-test",
            config=load_config({}),
            stream_fn=_fake_stream(_result()),
        )
    )
    assert isinstance(summary, EvalSummary)
    assert len(summary.results) == 6
    assert len(summary.by_strategy()) == 2


def test_main_missing_api_key_exits_nonzero(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert main([]) == 1


def test_main_runs_end_to_end_with_fake_stream(monkeypatch, capsys) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

    async def fake_stream(
        prompt: str, *, strategy=None, model=None, api_key=None
    ) -> AsyncIterator[StreamChunk | StreamedResult]:
        yield _result()

    monkeypatch.setattr(evals_mod, "stream_chat_completion", fake_stream)
    monkeypatch.setattr(
        evals_mod, "record_trace", lambda **kwargs: TraceOutcome("disabled", None, None)
    )
    assert main(["--limit", "1"]) == 0
    out = capsys.readouterr().out
    assert "default" in out
    assert "cost" in out


def test_load_cases_reads_five_cases() -> None:
    cases = load_cases()
    assert len(cases) == 5
    assert [c.case_id for c in cases] == [
        "complaint-timeout-01",
        "complaint-ratelimit-03",
        "adversarial-guarantee-07",
        "adversarial-public-08",
        "edge-nofailure-12",
    ]


def test_format_summary_text_contains_per_strategy_lines(monkeypatch) -> None:
    monkeypatch.setattr(
        evals_mod, "record_trace", lambda **kwargs: TraceOutcome("disabled", None, None)
    )
    summary = _run(
        run_eval_set(
            load_cases()[:2],
            strategies=(DEFAULT_STRATEGY, COST_STRATEGY),
            api_key="sk-test",
            config=load_config({}),
            stream_fn=_fake_stream(_result()),
        )
    )
    text = evals_mod.format_summary(summary)
    assert "default" in text
    assert "cost" in text
    assert "passed" in text
    assert "complaint-timeout-01" in text


def test_format_summary_json_is_parseable(monkeypatch) -> None:
    monkeypatch.setattr(
        evals_mod, "record_trace", lambda **kwargs: TraceOutcome("disabled", None, None)
    )
    summary = _run(
        run_eval_set(
            load_cases(),
            strategies=(DEFAULT_STRATEGY, COST_STRATEGY),
            api_key="sk-test",
            config=load_config({}),
            stream_fn=_fake_stream(_result()),
        )
    )
    doc = json.loads(evals_mod.format_summary(summary, as_json=True))
    assert set(doc.keys()) == {"cases", "strategies", "results"}
    assert "default" in doc["strategies"]
    assert "cost" in doc["strategies"]
    assert len(doc["results"]) == 5 * 2


def test_run_eval_set_uses_models_override(monkeypatch) -> None:
    monkeypatch.setattr(
        evals_mod, "record_trace", lambda **kwargs: TraceOutcome("disabled", None, None)
    )
    models = ("openai/gpt-4o-mini", "meta-llama/llama-3.1-8b-instruct")
    summary = _run(
        run_eval_set(
            [_case("c1")],
            models=models,
            api_key="sk-test",
            config=load_config({}),
            stream_fn=_fake_stream(_result()),
        )
    )
    assert {r.strategy_name for r in summary.results} == set(models)
