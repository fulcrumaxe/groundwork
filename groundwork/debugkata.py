"""Debugging kata library (F-88): classic bug shapes, synthetic + real.

Eight classic bug shapes ship as synthetic katas (buggy/fixed pair
plus the failing call). ``katas_for`` matches a real lesson snippet
against each shape's regex — the REAL adapter — and attaches at most
two katas to the lesson frame; snippets matching nothing keep the
frame byte-identical (the legacy fallback). ``pipeline.create_module``
stamps the match at generation; the module page renders attached
katas per lesson. Stdlib only (``re``, ``html``); no I/O, never raises.
"""
from __future__ import annotations

import html
import re

STATUS_ANCHOR = "status-b20-debugkata"

MAX_KATAS = 2

SHAPES = (
    {"id": "off-by-one",
     "title": "Off by one",
     "buggy": "xs[len(xs)]",
     "fixed": "xs[len(xs) - 1]",
     "failing_call": "xs[len(xs)]  -> IndexError",
     "spot_rule": r"\[\s*len\(",
     "blurb": "indexes past the last element"},
    {"id": "wrong-operator",
     "title": "Wrong operator",
     "buggy": "if score = 10:",
     "fixed": "if score == 10:",
     "failing_call": "score = 10  -> SyntaxError",
     "spot_rule": r"if\s+[^:\n]*[^=!<>]=(?![=])",
     "blurb": "assigns where it should compare"},
    {"id": "mutable-default",
     "title": "Mutable default",
     "buggy": "def add(item, box=[]):",
     "fixed": "def add(item, box=None):",
     "failing_call": "add(1); add(2)  -> box keeps [1, 2]",
     "spot_rule": r"def\s+\w+\([^)]*=\s*(\[\]|\{\})",
     "blurb": "one list shared across calls"},
    {"id": "none-deref",
     "title": "None dereference",
     "buggy": "user = None\nuser.name",
     "fixed": "user = load()\nuser.name if user else '?'",
     "failing_call": "None.name  -> AttributeError",
     "spot_rule": r"=\s*None\b",
     "blurb": "a None flows into attribute access"},
    {"id": "swallowed-exception",
     "title": "Swallowed exception",
     "buggy": "try:\n    save(row)\nexcept Exception:\n    pass",
     "fixed": "try:\n    save(row)\nexcept IOError:\n    retry(row)",
     "failing_call": "save(bad)  -> silence, row lost",
     "spot_rule": r"except(?:\s+Exception)?\s*:[^\n]*\n\s*pass",
     "blurb": "every failure vanishes into pass"},
    {"id": "fencepost-range",
     "title": "Fencepost range",
     "buggy": "for i in range(len(xs)):\n    use(xs[i + 1])",
     "fixed": "for i in range(len(xs) - 1):\n    use(xs[i + 1])",
     "failing_call": "last i  -> IndexError",
     "spot_rule": r"range\(",
     "blurb": "the last step walks off the end"},
    {"id": "aliasing-mutation",
     "title": "Aliasing mutation",
     "buggy": "box.append(item)",
     "fixed": "box = box + [item]",
     "failing_call": "shared.append(1)  -> every alias sees it",
     "spot_rule": r"\.append\(",
     "blurb": "mutates a list someone else holds"},
    {"id": "int-division",
     "title": "Integer division",
     "buggy": "half = total / 2",
     "fixed": "half = total // 2",
     "failing_call": "5 / 2  -> 2.5, not 2",
     "spot_rule": r"(?<!/)/(?![/=])",
     "blurb": "float division where an int belongs"},
)
BY_ID = {s["id"]: s for s in SHAPES}


def list_shapes() -> list:
    """Shape ids in catalog order; never raises."""
    try:
        return [s["id"] for s in SHAPES]
    except Exception:  # noqa: BLE001
        return []


def kata_by_id(shape_id):
    """Shape entry or None; never raises."""
    try:
        return BY_ID.get(shape_id)
    except Exception:  # noqa: BLE001
        return None


def _snippet_text(snippet) -> str:
    try:
        if snippet is None:
            return ""
        if isinstance(snippet, str):
            return snippet
        return "\n".join(str(l) for l in snippet)
    except Exception:  # noqa: BLE001
        return ""


def katas_for(concept, snippet, ctx=None) -> list:
    """Up to two katas whose shape matches the snippet; [] otherwise.

    ``concept``/``ctx`` are accepted for the pipeline call shape and
    ignored by the matcher. Never raises.
    """
    _ = concept, ctx
    try:
        text = _snippet_text(snippet)
        if not text.strip():
            return []
        out = []
        for shape in SHAPES:
            try:
                if re.search(shape["spot_rule"], text):
                    out.append({k: shape[k] for k in
                                ("id", "title", "buggy", "fixed",
                                 "failing_call", "blurb")})
            except re.error:
                continue
            if len(out) >= MAX_KATAS:
                break
        return out
    except Exception:  # noqa: BLE001
        return []


def enrich_lesson(lesson: dict, snippet) -> dict:
    """Stamp matched katas onto the frame; frame untouched when none."""
    try:
        if not isinstance(lesson, dict):
            return lesson
        matched = katas_for(lesson.get("name", ""), snippet)
        if not matched:
            return lesson
        lesson["kata"] = matched
        return lesson
    except Exception:  # noqa: BLE001
        return lesson


def render_kata(kata: dict) -> str:
    """One kata as HTML; "" on hostile input."""
    try:
        if not isinstance(kata, dict) or not kata.get("id"):
            return ""
        esc = html.escape
        return (
            f"<div class='debugkata'><h5>{esc(kata.get('title', kata['id']))}</h5>"
            f"<p><small>{esc(kata.get('blurb', ''))}</small></p>"
            f"<pre>buggy: {esc(kata.get('buggy', ''))}\n"
            f"fixed: {esc(kata.get('fixed', ''))}</pre>"
            f"<p><small>Failing call: <code>{esc(kata.get('failing_call', ''))}</code></small></p></div>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def lesson_block(lesson: dict) -> str:
    """Attached katas for one lesson frame; "" when none attached."""
    try:
        if not isinstance(lesson, dict):
            return ""
        katas = lesson.get("kata")
        if not isinstance(katas, list) or not katas:
            return ""
        return "".join(render_kata(k) for k in katas[:MAX_KATAS])
    except Exception:  # noqa: BLE001
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch20 home module."""
    sample = render_kata(kata_by_id("fencepost-range"))
    shapes = ", ".join(html.escape(s) for s in list_shapes())
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Debugging kata library <small>(feature)</small></h3>"
        "<p>Meet the eight classic bug shapes with a failing call each, "
        "drawn from synthetic and real code. "
        "<code>groundwork/debugkata.py</code> matches each lesson's own "
        "snippet against the shape catalog at generation "
        "(<code>pipeline.create_module</code>) and the module page shows "
        "attached katas per lesson. Shapes: "
        f"{shapes}. A live sample renders below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "debugkata-library",
        "kind": "feature",
        "title": "Debugging kata library",
        "blurb": "Meet the eight classic bug shapes with a failing call "
                 "each, drawn from synthetic and real code.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
