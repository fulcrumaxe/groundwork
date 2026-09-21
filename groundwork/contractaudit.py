"""Type-contract live registry (F-50 CI gate input).

Derives the six-part registry from the real code — GENERATORS keys,
grade/widget dispatch branches, the disclosure table, the pipeline
emission map, and the e2e answer dispatch — so the audit gate fails
when a type ships without a part, not when a hand-kept list drifts.
The Status demo eats live_report(); the CI gate test pins the
baseline. Never raises; never touches the DB.
"""
from __future__ import annotations

import inspect
import re


def _num_branches(src: str, var: str) -> set:
    """Ints dispatched as ``if <var> == N`` / ``if <var> in (A, B)``."""
    try:
        out = set(map(int, re.findall(r"\b%s\s*==\s*(\d+)" % var, src)))
        for group in re.findall(r"\b%s\s+in\s+\(([^)]*)\)" % var, src):
            out |= set(map(int, re.findall(r"\d+", group)))
        return out
    except Exception:  # noqa: BLE001 — parsing never raises
        return set()


def _quoted_branches(src: str) -> set:
    """Ints dispatched as ``etype == "N"`` / ``etype in ("A", ...)``."""
    try:
        out = set(map(int, re.findall(r"\betype\s*==\s*[\"'](\d+)[\"']", src)))
        for group in re.findall(r"\betype\s+in\s+\(([^)]*)\)", src):
            out |= set(map(int, re.findall(r"\d+", group)))
        return out
    except Exception:  # noqa: BLE001 — parsing never raises
        return set()


def live_registry() -> dict:
    """Six-part registry derived from live code; never raises."""
    from . import cards as cardsmod
    from . import exercises as exmod
    from . import grading as gradingmod
    from . import pipeline as pipelinemod
    from . import __main__ as mainmod
    try:
        types = set(exmod.TYPES)
        try:
            graded = _num_branches(inspect.getsource(exmod.grade), "t")
        except (OSError, TypeError):
            graded = set()
        try:
            widgets = _quoted_branches(
                inspect.getsource(cardsmod.answer_widget))
        except (OSError, TypeError):
            widgets = set()
        try:
            fallback = gradingmod.disclosure("no-such-type")
            disclosed = {t for t in types
                         if gradingmod.disclosure(t) != fallback}
        except Exception:  # noqa: BLE001 — probe never raises
            disclosed = set()
        try:
            emitted = set(sum(pipelinemod.BLOOM_DEFAULT_TYPES.values(), []))
        except Exception:  # noqa: BLE001 — map read never raises
            emitted = set()
        try:
            e2e = _num_branches(inspect.getsource(mainmod.cmd_e2e), "t")
        except (OSError, TypeError):
            e2e = set()
        return {"generator": set(exmod.GENERATORS),
                "grader": graded,
                "widget": widgets,
                "disclosure": disclosed,
                "emission": emitted,
                "e2e": e2e}
    except Exception:  # noqa: BLE001 — registry never raises
        return {}


def live_report() -> list:
    """audit_type() row per registered exercise type; never raises."""
    from . import exercises as exmod
    from . import typecontract as tcmod
    try:
        reg = live_registry()
        return [tcmod.audit_type(t, reg) for t in sorted(exmod.TYPES)]
    except Exception:  # noqa: BLE001 — report never raises
        return []
