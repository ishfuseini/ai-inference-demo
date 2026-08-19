"""UI controls for routing strategy selection and fallback rule editing.

Minimal stub: functions to render controls in the existing demo UI.
"""

from typing import List


def render_strategy_selector(strategies: List[str], selected: str):
    """Return a minimal representation of selector state for tests/demo.

    In the real UI this would render widgets; for now return dict.
    """
    return {"strategies": strategies, "selected": selected}


def render_fallback_editor(fallbacks: List[str]):
    return {"fallbacks": fallbacks}
