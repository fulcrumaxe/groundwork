"""Inline SVG call graphs replacing text lists (I-126).

Lesson dicts from pipeline.lesson_for carry callers/callees name
lists (<=8 each, from graph.py edges). graph_svg() draws them
instead: callers column left, self center, callees column right,
arrows showing call direction. Pure functions, stdlib only (html);
no I/O, never raises. Legacy no-data lessons get '' so pages stay
byte-identical.

Caller path (real learner/reader, never a Status demo): lesson
rendering — Handler.module_html appends block_html(lesson_map[node])
beside the diagrams badge_html call, so every lesson with call data
grows a graph. No other web.py edits.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b21-callgraph"

#: Cap per side so one hub function cannot stretch the page.
MAX_SIDE = 5

BOX_W = 100
BOX_H = 20
ROW_H = 30
PAD = 8
LABEL_CHARS = 14


def _names(value, cap=MAX_SIDE) -> list:
    """Clean name list, deduped, capped; never raises."""
    try:
        if not isinstance(value, (list, tuple)):
            return []
        out = []
        for v in value:
            if isinstance(v, str) and v.strip():
                s = v.strip().split(":")[-1]
                if s not in out:
                    out.append(s)
                if len(out) >= cap:
                    break
        return out
    except Exception:  # noqa: BLE001 -- audit must never raise
        return []


def callers_of(lesson) -> list:
    """Caller names for a lesson dict; [] for anything else."""
    try:
        if isinstance(lesson, dict):
            return _names(lesson.get("callers"))
        return []
    except Exception:  # noqa: BLE001 -- audit must never raise
        return []


def callees_of(lesson) -> list:
    """Callee names for a lesson dict; [] for anything else."""
    try:
        if isinstance(lesson, dict):
            return _names(lesson.get("callees"))
        return []
    except Exception:  # noqa: BLE001 -- audit must never raise
        return []


def has_graph(lesson) -> bool:
    """True when a lesson carries any call data."""
    try:
        return bool(callers_of(lesson) or callees_of(lesson))
    except Exception:  # noqa: BLE001 -- audit must never raise
        return False


def _label(name) -> str:
    """Short display label; overlong names gain an ellipsis."""
    try:
        s = str(name or "")
        if len(s) <= LABEL_CHARS:
            return s
        return s[:LABEL_CHARS - 1] + "…"
    except Exception:  # noqa: BLE001 -- audit must never raise
        return ""


def graph_svg(lesson, self_name="") -> str:
    """Inline SVG: callers left, self center, callees right.

    '' for lessons without call data (legacy path stays
    byte-identical) and for anything unparseable. Never raises.
    """
    try:
        if not isinstance(lesson, dict):
            return ""
        callers = callers_of(lesson)
        callees = callees_of(lesson)
        if not (callers or callees):
            return ""
        self_l = _label(self_name or lesson.get("name") or "self")
        rows = max(len(callers), len(callees), 1)
        width = PAD * 2 + BOX_W * 3 + 40
        height = rows * ROW_H + 34
        x0 = PAD
        x1 = PAD + BOX_W + 20
        x2 = PAD + (BOX_W + 20) * 2

        def box(x, y, text, cls):
            return (
                f"<g class='{cls}'><rect x='{x}' y='{y}' "
                f"width='{BOX_W}' height='{BOX_H}' rx='4'></rect>"
                f"<text x='{x + BOX_W / 2}' y='{y + 14}' "
                f"text-anchor='middle'>{html.escape(_label(text))}"
                f"<title>{html.escape(str(text))}</title></text></g>")

        parts = [
            f"<svg class='callgraph' role='img' "
            f"aria-label='Call graph for {html.escape(self_l)}' "
            f"width='{width}' height='{height}' "
            f"viewBox='0 0 {width} {height}' "
            "style='max-width:100%;height:auto'>",
            "<defs><marker id='cg-arrow' viewBox='0 0 10 10' "
            "refX='9' refY='5' markerWidth='7' markerHeight='7' "
            "orient='auto-start-reverse'>"
            "<path d='M0,0L10,5L0,10z' fill='currentColor'/>"
            "</marker></defs>",
            f"<title>Callers of and calls from {html.escape(self_l)}</title>",
        ]
        scy = 26 + (rows - 1) * ROW_H / 2
        parts.append(box(x1, scy, self_l, "cg-self"))
        for i, c in enumerate(callers):
            y = 26 + i * ROW_H
            parts.append(box(x0, y, c, "cg-caller"))
            parts.append(
                f"<line x1='{x0 + BOX_W}' y1='{y + BOX_H / 2}' "
                f"x2='{x1}' y2='{scy + BOX_H / 2}' "
                "marker-end='url(#cg-arrow)'/>")
        for i, c in enumerate(callees):
            y = 26 + i * ROW_H
            parts.append(box(x2, y, c, "cg-callee"))
            parts.append(
                f"<line x1='{x1 + BOX_W}' y1='{scy + BOX_H / 2}' "
                f"x2='{x2}' y2='{y + BOX_H / 2}' "
                "marker-end='url(#cg-arrow)'/>")
        parts.append("</svg>")
        return "".join(parts)
    except Exception:  # noqa: BLE001 -- render must never raise
        return ""


def block_html(lesson) -> str:
    """Figure wrapper for the lesson path; '' without call data."""
    try:
        svg = graph_svg(lesson)
        if not svg:
            return ""
        if isinstance(lesson, dict):
            name = html.escape(str(lesson.get("name") or ""))
        else:
            name = ""
        return (
            "<figure class='callgraph-wrap'><figcaption><small>"
            f"Call graph for <code>{name}</code></small>"
            f"</figcaption>{svg}</figure>")
    except Exception:  # noqa: BLE001 -- render must never raise
        return ""


def section_html() -> str:
    """Status-page subsection with a live sample."""
    try:
        sample = block_html({"name": "f", "callers": ["a", "b"],
                             "callees": ["c"]})
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Inline SVG call graphs "
            "<small>(improvement)</small></h3>"
            "<p>Caller/callee text lists render as an inline SVG "
            "instead: callers left, self center, callees right, arrows "
            "for direction (<code>groundwork/callgraph.py</code> on the "
            "module rendering path). Lessons without call data render "
            "nothing extra. A live sample renders below.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must never raise
        return (f"<h3 id='{STATUS_ANCHOR}'>Inline SVG call graphs</h3>"
                "<p>Call-graph help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "callgraph-svg",
        "kind": "improvement",
        "title": "Call graphs as inline SVG",
        "blurb": "Caller/callee lists render as a small inline SVG graph per lesson.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
