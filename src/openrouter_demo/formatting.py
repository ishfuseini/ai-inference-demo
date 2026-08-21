"""Shared value-formatting helpers for Unawareable values.

Both `evals.py` (console text output) and `ui.py` (browser display) format
`Unavailable` sentinel values to human-readable strings. The formatting of
the *available* value is the same in both places; only the fallback string
differs. These helpers factor out the shared formatting logic.
"""

from __future__ import annotations

from openrouter_demo.models import Unavailable


def is_unavailable(value: object) -> bool:
    """True when value is an `Unavailable` sentinel or `None`."""
    return isinstance(value, Unavailable) or value is None


def format_cost(value: float | Unavailable | None, *, unavailable: str) -> str:
    if is_unavailable(value):
        return unavailable
    return f"${value:g}"


def format_number(value: float | int | Unavailable | None, *, unavailable: str) -> str:
    if is_unavailable(value):
        return unavailable
    return f"{value:g}"


def format_latency(value: float | int | Unavailable | None, *, unavailable: str) -> str:
    formatted = format_number(value, unavailable=unavailable)
    return formatted if is_unavailable(value) else f"{formatted} ms"


def format_trace(value: str | Unavailable | None, *, unavailable: str) -> str:
    if is_unavailable(value):
        return unavailable
    return value
