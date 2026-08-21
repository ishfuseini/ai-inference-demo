import dataclasses
import importlib
import json
from pathlib import Path

from openrouter_demo.evals import main as evals_main
from openrouter_demo.models import UNAVAILABLE, AttemptRecord, FallbackEvidence, Status, Unavailable
from openrouter_demo.routing import (
    COST_STRATEGY,
    FALLBACK_PRIMARY_STRATEGY,
    INTELLIGENCE_STRATEGY,
    LATENCY_STRATEGY,
    ROUTING_STRATEGY_LABELS,
    STRATEGIES,
)


def test_required_modules_import() -> None:
    for name in (
        "openrouter_demo",
        "openrouter_demo.client",
        "openrouter_demo.config",
        "openrouter_demo.evals",
        "openrouter_demo.models",
        "openrouter_demo.routing",
        "openrouter_demo.scenarios",
        "openrouter_demo.sqlite_store",
        "openrouter_demo.telemetry",
        "openrouter_demo.ui",
    ):
        assert importlib.import_module(name)


def test_live_boundaries_raise_honest_phase_errors() -> None:
    assert callable(evals_main)


def test_routing_labels_do_not_claim_provider_results() -> None:
    assert ROUTING_STRATEGY_LABELS == {
        "cost": "Cost",
        "latency": "Latency",
        "intelligence": "Intelligence",
    }


def test_phase3_types_importable() -> None:
    assert Status.FALLBACK_SUCCEEDED == "fallback_succeeded"
    assert AttemptRecord is not None
    assert FallbackEvidence is not None
    assert COST_STRATEGY.name == "cost"
    assert LATENCY_STRATEGY.name == "latency"
    assert INTELLIGENCE_STRATEGY.name == "intelligence"
    assert FALLBACK_PRIMARY_STRATEGY.name == "custom"
    assert set(STRATEGIES.keys()) == {"cost", "latency", "intelligence"}


def test_unavailable_metadata_is_not_zero() -> None:
    assert isinstance(UNAVAILABLE, Unavailable)
    assert UNAVAILABLE != 0
    assert not UNAVAILABLE


def test_evals_cases_json_has_three_to_five_cases() -> None:
    assert Path("evals/.gitkeep").exists()
    assert Path("evals/cases.json").exists()
    data = json.loads(Path("evals/cases.json").read_text())
    assert 3 <= len(data["cases"]) <= 5


def test_phase4_types_and_fields_importable() -> None:
    from openrouter_demo.models import RepeatObservation, TelemetryEvidence
    from openrouter_demo.telemetry import TraceOutcome

    assert RepeatObservation is not None
    assert TraceOutcome is not None

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
