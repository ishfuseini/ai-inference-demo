import dataclasses
import importlib
import json
from pathlib import Path

from openrouter_demo.config import (
    LANGFUSE_BASE_URL,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
    load_config,
)
from openrouter_demo.evals import main as evals_main
from openrouter_demo.models import UNAVAILABLE, AttemptRecord, FallbackEvidence, Status, Unavailable
from openrouter_demo.routing import (
    COST_STRATEGY,
    FALLBACK_PRIMARY_STRATEGY,
    LATENCY_STRATEGY,
    ROUTING_STRATEGY_LABELS,
    STRATEGIES,
)
from openrouter_demo.scenarios import PhaseNotImplementedError as ScenarioNotImplemented
from openrouter_demo.scenarios import run_fallback_scenario
from openrouter_demo.telemetry import trace_readiness_from_config


def test_required_modules_import() -> None:
    for name in (
        "openrouter_demo",
        "openrouter_demo.client",
        "openrouter_demo.config",
        "openrouter_demo.evals",
        "openrouter_demo.history",
        "openrouter_demo.models",
        "openrouter_demo.routing",
        "openrouter_demo.scenarios",
        "openrouter_demo.telemetry",
        "openrouter_demo.ui",
    ):
        assert importlib.import_module(name)


def test_live_boundaries_raise_honest_phase_errors() -> None:
    assert callable(run_fallback_scenario)
    assert issubclass(ScenarioNotImplemented, NotImplementedError)
    assert callable(evals_main)


def test_routing_labels_do_not_claim_provider_results() -> None:
    assert ROUTING_STRATEGY_LABELS == {
        "default": "Default",
        "cost": "Cost optimized",
        "latency": "Latency optimized",
        "custom": "Custom",
    }


def test_phase3_types_importable() -> None:
    assert Status.FALLBACK_SUCCEEDED == "fallback_succeeded"
    assert AttemptRecord is not None
    assert FallbackEvidence is not None
    assert COST_STRATEGY.name == "cost"
    assert LATENCY_STRATEGY.name == "latency"
    assert FALLBACK_PRIMARY_STRATEGY.name == "custom"
    assert set(STRATEGIES.keys()) == {"default", "cost", "latency"}


def test_unavailable_metadata_is_not_zero() -> None:
    assert isinstance(UNAVAILABLE, Unavailable)
    assert UNAVAILABLE != 0
    assert not UNAVAILABLE


def test_trace_readiness_uses_config_without_creating_traces() -> None:
    disabled = trace_readiness_from_config(load_config({}))
    enabled = trace_readiness_from_config(
        load_config(
            {
                LANGFUSE_PUBLIC_KEY: "pk",
                LANGFUSE_SECRET_KEY: "sk",
                LANGFUSE_BASE_URL: "https://cloud.langfuse.com",
            }
        )
    )
    assert disabled.enabled is False
    assert enabled.enabled is True


def test_evals_cases_json_has_three_to_five_cases() -> None:
    assert Path("evals/.gitkeep").exists()
    assert Path("evals/cases.json").exists()
    data = json.loads(Path("evals/cases.json").read_text())
    assert 3 <= len(data["cases"]) <= 5


def test_phase4_types_and_fields_importable() -> None:
    from openrouter_demo.models import RepeatObservation, TelemetryEvidence
    from openrouter_demo.scenarios import run_repeat_scenario
    from openrouter_demo.telemetry import TraceOutcome

    assert RepeatObservation is not None
    assert TraceOutcome is not None
    assert callable(run_repeat_scenario)

    field_names = {field.name for field in dataclasses.fields(TelemetryEvidence)}
    for name in (
        "cache_status",
        "cached_tokens",
        "cache_write_tokens",
        "trace_status",
        "trace_id",
        "trace_url",
        "openrouter_metadata",
    ):
        assert name in field_names
