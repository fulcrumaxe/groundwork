"""Diagrams-per-lesson quality gate (I-125): every lesson gets a visual.

``visuals_in`` counts diagram/trace/code/figure evidence on a lesson
dict; lessons with study text but zero visuals fail the gate and get
a badge on the module rendering path until fixed. Empty/hostile
lessons pass vacuously so legacy pages stay byte-identical. Stdlib
only (``html``); no I/O, never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b20-diagrams"

VISUAL_KINDS = ("diagram", "trace", "code", "figure")


def _nonempty_str(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def visuals_in(lesson) -> dict:
    """{kind: bool} visual evidence; all False on hostile input."""
    found = {kind: False for kind in VISUAL_KINDS}
    try:
        if not isinstance(lesson, dict):
            return found
        dual = lesson.get("dualcode")
        if isinstance(dual, dict):
            steps = dual.get("steps")
            found["diagram"] = isinstance(steps, list) and any(
                isinstance(s, str) and s.strip() for s in steps)
        worked = lesson.get("worked")
        if isinstance(worked, dict):
            trace = worked.get("trace")
            if isinstance(trace, dict):
                steps = trace.get("steps")
                found["trace"] = isinstance(steps, list) and len(steps) > 0
        found["code"] = _nonempty_str(lesson.get("source")) or _nonempty_str(
            lesson.get("key_lines"))
        found["figure"] = bool(lesson.get("figure"))
        return found
    except Exception:  # noqa: BLE001
        return found


def needs_visual(lesson) -> bool:
    """True iff a non-empty lesson dict carries zero visuals."""
    try:
        if not isinstance(lesson, dict) or not lesson:
            return False
        return not any(visuals_in(lesson).values())
    except Exception:  # noqa: BLE001
        return False


def gate_lesson(lesson) -> dict:
    """{"ok", "missing", "visuals"} for one lesson; never raises."""
    try:
        found = visuals_in(lesson)
        missing = [k for k, v in found.items() if not v]
        ok = not needs_visual(lesson)
        return {"ok": ok, "missing": [] if ok else missing,
                "visuals": sum(1 for v in found.values() if v)}
    except Exception:  # noqa: BLE001
        return {"ok": True, "missing": [], "visuals": 0}


def gate_module(lesson_map) -> dict:
    """{"per-lesson", "failing"} over a {node: lesson} map."""
    try:
        per = {}
        if isinstance(lesson_map, dict):
            for node, lesson in lesson_map.items():
                per[node] = gate_lesson(lesson)
        failing = sorted(n for n, g in per.items() if not g["ok"])
        return {"per-lesson": per, "failing": failing}
    except Exception:  # noqa: BLE001
        return {"per-lesson": {}, "failing": []}


def badge_html(lesson) -> str:
    """'Needs a visual' notice for failing lessons; "" otherwise."""
    try:
        gate = gate_lesson(lesson)
        if gate["ok"]:
            return ""
        missing = ", ".join(gate["missing"])
        return (
            f"<p class='needs-visual'>Needs a visual: no {html.escape(missing)} "
            f"yet — add a diagram, trace, code snippet, or figure.</p>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def toc_mark(lesson) -> str:
    """" · needs visual" chip for failing lessons; "" otherwise."""
    try:
        return " · needs visual" if needs_visual(lesson) else ""
    except Exception:  # noqa: BLE001
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch20 home module."""
    sample = badge_html({"summary": "A lesson with words but no picture."})
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Every lesson gets a visual <small>(improvement)</small></h3>"
        "<p>Lessons missing a visual are flagged until fixed. "
        "<code>groundwork/diagrams.py</code> counts diagram, trace, code, "
        "and figure evidence on the module rendering path "
        "(<code>Handler.module_html</code>); passing lessons render "
        "nothing extra. A live sample renders below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "diagrams-gate",
        "kind": "improvement",
        "title": "Every lesson gets a visual",
        "blurb": "Lessons missing a visual are flagged until fixed.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
