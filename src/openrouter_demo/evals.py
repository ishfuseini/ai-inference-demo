from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass

from openrouter_demo.client import OpenRouterError, stream_chat_completion
from openrouter_demo.config import AppConfig, load_config
from openrouter_demo.models import (
    StreamChunk,
    StreamedResult,
    TelemetryEvidence,
    Unavailable,
)
from openrouter_demo.routing import STRATEGIES, RoutingStrategy
from openrouter_demo.telemetry import record_trace

type StreamFn = Callable[..., AsyncIterator[StreamChunk | StreamedResult]]


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    name: str
    prompt: str
    expected_terms: tuple[str, ...]
    forbidden_terms: tuple[str, ...]
    scoring_notes: str = ""


@dataclass(frozen=True)
class EvalResult:
    case_id: str
    run_id: str
    strategy_name: str
    passed: bool
    score_reason: str
    matched_terms: tuple[str, ...]
    missed_terms: tuple[str, ...]
    tripped_terms: tuple[str, ...]
    telemetry: TelemetryEvidence | None = None


@dataclass(frozen=True)
class EvalSummary:
    results: tuple[EvalResult, ...]

    def by_strategy(self) -> dict[str, list[EvalResult]]:
        grouped: dict[str, list[EvalResult]] = {}
        for result in self.results:
            grouped.setdefault(result.strategy_name, []).append(result)
        return grouped


def score_response(
    case: EvalCase, text: str
) -> tuple[bool, str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    lowered = text.lower()
    matched = tuple(term for term in case.expected_terms if term.lower() in lowered)
    missed = tuple(term for term in case.expected_terms if term.lower() not in lowered)
    tripped = tuple(term for term in case.forbidden_terms if term.lower() in lowered)
    passed = not missed and not tripped
    parts: list[str] = []
    if matched:
        parts.append(f"matched: {', '.join(matched)}")
    if missed:
        parts.append(f"missing: {', '.join(missed)}")
    if tripped:
        parts.append(f"forbidden: {', '.join(tripped)}")
    reason = "; ".join(parts) or "no evidence"
    return passed, reason, matched, missed, tripped


def load_cases(path: str = "evals/cases.json") -> list[EvalCase]:
    with open(path, encoding="utf-8") as file:
        raw = json.load(file)["cases"]
    cases = [
        EvalCase(
            case_id=item["case_id"],
            name=item["name"],
            prompt=item["prompt"],
            expected_terms=tuple(item["expected_terms"]),
            forbidden_terms=tuple(item.get("forbidden_terms", ())),
            scoring_notes=item.get("scoring_notes", ""),
        )
        for item in raw
    ]
    if not (3 <= len(cases) <= 5):
        raise ValueError(f"expected 3-5 eval cases, found {len(cases)}")
    return cases


async def run_eval_case(
    case: EvalCase,
    *,
    strategy: RoutingStrategy | None = None,
    model: str | None = None,
    api_key: str,
    config: AppConfig,
    stream_fn: StreamFn = stream_chat_completion,
) -> EvalResult:
    strategy_name = strategy.name if strategy is not None else (model or "")
    final_result: StreamedResult | None = None
    try:
        if strategy is not None:
            async for event in stream_fn(case.prompt, strategy=strategy, api_key=api_key):
                if isinstance(event, StreamedResult):
                    final_result = event
        else:
            async for event in stream_fn(case.prompt, model=model, api_key=api_key):
                if isinstance(event, StreamedResult):
                    final_result = event
    except OpenRouterError as exc:
        return EvalResult(case.case_id, "", strategy_name, False, str(exc), (), (), (), None)

    if final_result is None:
        return EvalResult(
            case.case_id,
            "",
            strategy_name,
            False,
            "stream ended without a final result",
            (),
            (),
            (),
            None,
        )

    model_for_trace = (
        final_result.model
        if not isinstance(final_result.model, Unavailable)
        else (strategy.model if strategy is not None else (model or "unknown"))
    )
    usage_details: dict[str, int] = {}
    if not isinstance(final_result.prompt_tokens, Unavailable):
        usage_details["prompt_tokens"] = final_result.prompt_tokens
    if not isinstance(final_result.completion_tokens, Unavailable):
        usage_details["completion_tokens"] = final_result.completion_tokens

    outcome = record_trace(
        config=config,
        name=f"eval-{case.case_id}",
        model=model_for_trace,
        input={"prompt": case.prompt},
        output=final_result.text,
        usage_details=usage_details,
    )

    telemetry = TelemetryEvidence(
        model=final_result.model,
        provider=final_result.provider,
        latency_ms=final_result.latency_ms,
        prompt_tokens=final_result.prompt_tokens,
        completion_tokens=final_result.completion_tokens,
        total_tokens=final_result.total_tokens,
        cost_usd=final_result.cost_usd,
        cache_status=final_result.cache_status,
        cached_tokens=final_result.cached_tokens,
        cache_write_tokens=final_result.cache_write_tokens,
        openrouter_metadata=final_result.openrouter_metadata,
        trace_status=outcome.status,
        trace_id=outcome.trace_id,
        trace_url=outcome.trace_url,
    )

    passed, reason, matched, missed, tripped = score_response(case, final_result.text)
    return EvalResult(
        case.case_id,
        uuid.uuid4().hex,
        strategy_name,
        passed,
        reason,
        matched,
        missed,
        tripped,
        telemetry,
    )


async def run_eval_set(
    cases: list[EvalCase],
    *,
    strategies: tuple[RoutingStrategy, ...] = (),
    models: tuple[str, ...] = (),
    api_key: str,
    config: AppConfig,
    stream_fn: StreamFn = stream_chat_completion,
) -> EvalSummary:
    results: list[EvalResult] = []
    for case in cases:
        if models:
            for model_id in models:
                results.append(
                    await run_eval_case(
                        case, model=model_id, api_key=api_key, config=config, stream_fn=stream_fn
                    )
                )
        else:
            for strategy in strategies:
                results.append(
                    await run_eval_case(
                        case, strategy=strategy, api_key=api_key, config=config, stream_fn=stream_fn
                    )
                )
    return EvalSummary(tuple(results))


def _fmt_cost(value: float | Unavailable | None) -> str:
    if isinstance(value, Unavailable) or value is None:
        return "unavailable"
    return f"${value:g}"


def _fmt_num(value: float | Unavailable | None) -> str:
    if isinstance(value, Unavailable) or value is None:
        return "unavailable"
    return f"{value:g}"


def _fmt_latency(value: float | Unavailable | None) -> str:
    if isinstance(value, Unavailable) or value is None:
        return "unavailable"
    return f"{value:g} ms"


def _fmt_trace(value: str | Unavailable | None) -> str:
    if isinstance(value, Unavailable) or value is None:
        return "unavailable"
    return value


def _aggregate(results: list[EvalResult]) -> dict[str, object]:
    passed = sum(1 for result in results if result.passed)
    total = len(results)
    costs = [
        result.telemetry.cost_usd
        for result in results
        if result.telemetry is not None and not isinstance(result.telemetry.cost_usd, Unavailable)
    ]
    total_cost: float | None = sum(costs) if costs else None
    latencies = [
        result.telemetry.latency_ms
        for result in results
        if result.telemetry is not None and not isinstance(result.telemetry.latency_ms, Unavailable)
    ]
    mean_latency: float | None = round(sum(latencies) / len(latencies), 1) if latencies else None
    trace_statuses = [
        result.telemetry.trace_status
        for result in results
        if result.telemetry is not None and not isinstance(result.telemetry.trace_status, Unavailable)
    ]
    if any(status == "enabled" for status in trace_statuses):
        trace_state = "enabled"
    elif trace_statuses and all(status == "disabled" for status in trace_statuses):
        trace_state = "disabled"
    else:
        trace_state = "failed"
    return {
        "passed": passed,
        "total": total,
        "total_cost": total_cost,
        "mean_latency": mean_latency,
        "trace_state": trace_state,
    }


def format_summary(summary: EvalSummary, *, as_json: bool = False) -> str:
    by_strategy = summary.by_strategy()
    strategy_names = list(by_strategy.keys())
    case_ids = list(dict.fromkeys(result.case_id for result in summary.results))

    if as_json:
        strategies_doc: dict[str, dict[str, object]] = {}
        for name, results in by_strategy.items():
            agg = _aggregate(results)
            strategies_doc[name] = {
                "passed": agg["passed"],
                "total": agg["total"],
                "total_cost_usd": agg["total_cost"],
                "mean_latency_ms": agg["mean_latency"],
                "trace_status": agg["trace_state"],
            }
        doc = {
            "cases": case_ids,
            "results": [
                {
                    "case_id": result.case_id,
                    "strategy_name": result.strategy_name,
                    "passed": result.passed,
                    "score_reason": result.score_reason,
                    "telemetry": result.telemetry.to_dict() if result.telemetry is not None else None,
                }
                for result in summary.results
            ],
            "strategies": strategies_doc,
        }
        return json.dumps(doc)

    lines: list[str] = []
    for name, results in by_strategy.items():
        agg = _aggregate(results)
        lines.append(
            f"{name}: {agg['passed']}/{agg['total']} passed, "
            f"cost {_fmt_cost(agg['total_cost'])}, "
            f"mean latency {_fmt_latency(agg['mean_latency'])}, "
            f"trace {agg['trace_state']}"
        )

    lines.append("Case" + "".join(f" | {name}" for name in strategy_names))
    grid: dict[tuple[str, str], EvalResult] = {
        (result.case_id, result.strategy_name): result for result in summary.results
    }
    for case_id in case_ids:
        row = case_id
        for name in strategy_names:
            result = grid.get((case_id, name))
            row += f" | {'pass' if result is not None and result.passed else 'fail'}"
        lines.append(row)

    for result in summary.results:
        if result.telemetry is not None:
            lines.append(
                f"{result.case_id} {result.strategy_name}: "
                f"{'pass' if result.passed else 'fail'} — {result.score_reason} | "
                f"latency {_fmt_latency(result.telemetry.latency_ms)} | "
                f"tokens {_fmt_num(result.telemetry.total_tokens)} | "
                f"cost {_fmt_cost(result.telemetry.cost_usd)} | "
                f"trace {_fmt_trace(result.telemetry.trace_status)}"
            )
        else:
            lines.append(
                f"{result.case_id} {result.strategy_name}: fail — {result.score_reason} | no telemetry"
            )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openrouter_demo.evals",
        description="Run the deterministic eval set.",
    )
    parser.add_argument("--cases", default="evals/cases.json", help="path to cases JSON")
    parser.add_argument(
        "--strategies", default="default,cost", help="comma-separated STRATEGIES keys"
    )
    parser.add_argument(
        "--models",
        default=None,
        help="comma-separated model ids (overrides --strategies)",
    )
    parser.add_argument("--limit", type=int, default=0, help="run at most N cases (0 = all)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        config = load_config()
        if not config.openrouter_ready:
            print("OPENROUTER_API_KEY is not set. Export it and retry.", file=sys.stderr)
            return 1

        args = build_parser().parse_args(argv)

        strategies: tuple[RoutingStrategy, ...] = ()
        models: tuple[str, ...] = ()
        if args.models:
            models = tuple(part.strip() for part in args.models.split(",") if part.strip())
            if not models:
                print("No models specified.", file=sys.stderr)
                return 1
        else:
            try:
                strategies = tuple(
                    STRATEGIES[part.strip()] for part in args.strategies.split(",") if part.strip()
                )
            except KeyError as exc:
                print(f"Unknown strategy: {exc.args[0]}", file=sys.stderr)
                return 1
            if not strategies:
                print("No strategies specified.", file=sys.stderr)
                return 1

        try:
            cases = load_cases(args.cases)
        except (FileNotFoundError, ValueError, KeyError) as exc:
            print(f"Could not load cases: {exc}", file=sys.stderr)
            return 1

        if args.limit > 0:
            cases = cases[: args.limit]

        api_key = os.environ["OPENROUTER_API_KEY"]
        summary = asyncio.run(
            run_eval_set(
                cases,
                strategies=strategies,
                models=models,
                api_key=api_key,
                config=config,
                stream_fn=stream_chat_completion,
            )
        )
        print(format_summary(summary, as_json=args.json))
        return 0
    except Exception as exc:  # noqa: BLE001 — top-level CLI boundary
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 2
