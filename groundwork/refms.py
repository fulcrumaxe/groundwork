"""Reference runtime on code-card results (I-182): measured ms, never invented.

Execution-graded cards report pass/fail with no sense of pace, so a
learner cannot tell an efficient answer from a sluggish one. This module
closes that gap at grade time: the reference harness for the card's type
is re-run through the existing ``SandboxRunner`` wrapped in
``perf_counter``, and the measured milliseconds ride the result dict as
``ref_ms`` to the result screen. Nothing is stored (no schema change)
and nothing is estimated: a failed run, a missing runner, or a card
without a runnable reference yields no key, and the render seam prints
nothing, so legacy output stays byte-identical. Stdlib only
(``time``, ``html``); never raises.
"""
from __future__ import annotations

import html
import time

STATUS_ANCHOR = "status-b27-refms"

EXECUTION_TYPES = (8, 11, 12, 14, 19, 20, 23)


def _code(value) -> str:
    """Non-blank code string, else ""."""
    if not isinstance(value, str) or not value.strip():
        return ""
    return value


def reference_code(ex_type, payload) -> str:
    """Runnable reference harness for an execution-graded card; "" otherwise.

    Type 8 runs its ``code`` snippet; harness types run reference +
    tests (type 14: ``fixed`` + tests; type 11: ``solution`` lines +
    tests). Both halves are required for harness types: a bare
    definition block's import time is not a solution runtime.
    """
    try:
        t = int(ex_type)  # cards store exercise_type as TEXT
    except (TypeError, ValueError):
        return ""
    try:
        if not isinstance(payload, dict):
            return ""
        if t == 8:
            return _code(payload.get("code"))
        if t in (12, 19, 23, 20):
            ref = _code(payload.get("reference"))
            tests = _code(payload.get("tests"))
            if not ref or not tests:
                return ""
            return ref + "\n" + tests
        if t == 14:
            fixed = _code(payload.get("fixed"))
            tests = _code(payload.get("tests"))
            if not fixed or not tests:
                return ""
            return fixed + "\n" + tests
        if t == 11:
            sol = payload.get("solution", [])
            if isinstance(sol, list):
                sol = "\n".join(x for x in sol if isinstance(x, str))
            tests = _code(payload.get("tests"))
            if not _code(sol) or not tests:
                return ""
            return _code(sol) + "\n" + tests
        return ""
    except Exception:  # noqa: BLE001 -- lookup never raises
        return ""


def measure_ms(runner, code):
    """Wall-clock ms of ``runner.run(code)``; None when unmeasurable.

    Unmeasurable covers: no runner, unrunnable code, a run that
    raises, returns None, or reports ``ok == False``. Only a
    successful sandbox run produces a number.
    """
    try:
        if runner is None or not hasattr(runner, "run"):
            return None
        if not isinstance(code, str) or not code.strip():
            return None
        start = time.perf_counter()
        try:
            res = runner.run(code)
        finally:
            elapsed = time.perf_counter() - start
        if res is None or not getattr(res, "ok", False):
            return None
        return max(0, int(round(elapsed * 1000)))
    except Exception:  # noqa: BLE001 -- measuring never raises
        return None


def measure_for(ex_type, payload, runner):
    """Measured reference ms for a card; None when nothing measurable."""
    try:
        code = reference_code(ex_type, payload)
        if not code:
            return None
        return measure_ms(runner, code)
    except Exception:  # noqa: BLE001
        return None


def _valid_ms(value) -> bool:
    return (isinstance(value, int) and not isinstance(value, bool)
            and value >= 0)


def format_line(ms) -> str:
    """Plain-text runtime line; "" for anything but a measured int."""
    try:
        if not _valid_ms(ms):
            return ""
        if ms == 0:
            return "Reference runtime: <1 ms (measured)."
        return f"Reference runtime: {ms} ms (measured)."
    except Exception:  # noqa: BLE001
        return ""


def line_html(ref_ms) -> str:
    """Result-screen line for a measured value; "" when none/hostile."""
    try:
        line = format_line(ref_ms)
        if not line:
            return ""
        return f"<p><small>{html.escape(line)}</small></p>"
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def attach(result, ex_type, payload, runner):
    """Set ``result["ref_ms"]`` when measurable; same object, never raises.

    One-line grade-time seam: ``result = refms.attach(result, t, p,
    runner)``. The key appears only when a number was measured, so
    unmeasurable reviews keep their legacy dict shape.
    """
    try:
        if not isinstance(result, dict):
            return result
        ms = measure_for(ex_type, payload, runner)
        if ms is not None:
            result["ref_ms"] = ms
    except Exception:  # noqa: BLE001 -- attach never blocks grading
        pass
    return result


def _demo() -> str:
    """Static format sample; live values are measured at grade time.

    Deliberately not a live measurement: the Status page must render
    byte-identical across runs (pagesnap gate), and wall-clock ms
    never repeats. Grade-time measurement is proven by the
    CallerEffectTest, not by this illustration.
    """
    return ("<p><small>Sample rendering with an illustrative value "
            "(live values are measured at grade time): "
            "Reference runtime: 42 ms (measured).</small></p>")


def section_html() -> str:
    """Anchored status subsection; joined by the batch27 home module."""
    try:
        demo = _demo()
    except Exception:  # noqa: BLE001 -- status must always render
        demo = ""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Reference runtime "
        "<small>(improvement)</small></h3>"
        "<p>Code cards graded pass/fail with no sense of pace. "
        "<code>groundwork/refms.py</code> times the reference harness in "
        "the existing sandbox at grade time and shows the measured "
        "milliseconds on the result screen "
        "(<code>results.render_result</code>) -- calibrate your solution "
        "against the reference pace. Failed runs and non-executable cards "
        "show nothing, so legacy output stays byte-identical. A "
        "format sample renders below.</p>"
        f"{demo}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "reference-runtime",
        "kind": "improvement",
        "title": "Reference runtime",
        "blurb": "After a code card grades, the result shows the measured "
                 "reference runtime in ms -- calibrate your pace.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
