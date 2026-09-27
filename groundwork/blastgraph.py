"""Clickable blast-radius dependency graph (I-174).

Type 16 (blast-radius) answers today as a flat row of buttons:
cards.answer_widget turns each payload choice into one submit
button. This module renders the SAME choices as a small clickable
graph instead: the concept sits in a center box, one node per
choice fans out right, and SVG edges join them. Each node IS a
submit button posting the same name='answer' value, so grading
(exercises.grade type 16, exact answer text) is untouched and the
graph works with JS disabled. No new data source: choices come
from the stored payload only.

Caller path (real learner path, never a Status demo): the Due
queue and module pages both call cards.answer_widget, which
delegates etype "16" to branch_html here. Unusable payloads
render the legacy flat buttons byte-identical. Pure functions,
stdlib only (html, json); never raises.
"""
from __future__ import annotations

import html
import json

STATUS_ANCHOR = "status-b26-blastgraph"

#: Graph only when every choice fits on screen; more falls back
#: to the legacy row so no choice is ever unanswerable.
MAX_NODES = 6

BOX_W = 140
BOX_H = 22
ROW_H = 34
PAD = 8
GAP = 30
LABEL_CHARS = 20


def _field(card, name, default=""):
    """Field read for dict cards and sqlite Rows; default when missing."""
    try:
        if isinstance(card, dict):
            return card.get(name, default)
        return card[name]
    except (KeyError, IndexError, TypeError):
        return default


def _ok_list(items) -> list:
    """items when every entry is a graphable answer string, else []."""
    try:
        if not isinstance(items, list):
            return []
        out = [c for c in items if isinstance(c, str) and c.strip()]
        if len(out) != len(items) or not 2 <= len(out) <= MAX_NODES:
            return []
        return out
    except Exception:  # noqa: BLE001 -- audit must never raise
        return []


def _payload_of(card) -> dict:
    """Parsed payload for dicts and Rows; {} when missing/unparseable."""
    try:
        raw = _field(card, "payload", "{}")
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            parsed = json.loads(raw or "{}")
            return parsed if isinstance(parsed, dict) else {}
        return {}
    except (ValueError, TypeError):
        return {}


def usable_choices(payload) -> list:
    """Graphable choices from a parsed payload; [] unless 2..MAX strings."""
    try:
        if not isinstance(payload, dict):
            return []
        return _ok_list(payload.get("choices", []))
    except Exception:  # noqa: BLE001 -- audit must never raise
        return []


def has_graph(card, payload=None) -> bool:
    """True when this card can answer on the clickable graph."""
    try:
        p = payload if isinstance(payload, dict) else _payload_of(card)
        return bool(usable_choices(p))
    except Exception:  # noqa: BLE001 -- audit must never raise
        return False


def concept_of(card) -> str:
    """Center-node label; 'self' when the card carries no concept."""
    try:
        c = _field(card, "concept", "")
        if isinstance(c, str) and c.strip():
            return c.strip()
        return "self"
    except Exception:  # noqa: BLE001 -- audit must never raise
        return "self"


def _label(name) -> str:
    """Short ASCII display label; overlong names gain '...'."""
    try:
        s = str(name or "")
        if len(s) <= LABEL_CHARS:
            return s
        return s[:LABEL_CHARS - 3] + "..."
    except Exception:  # noqa: BLE001 -- audit must never raise
        return ""


def _uid(v) -> str:
    """Alphanumeric marker-id suffix; 'bg1' when empty/hostile."""
    try:
        return "".join(c for c in str(v or "bg1") if c.isalnum()) or "bg1"
    except Exception:  # noqa: BLE001 -- audit must never raise
        return "bg1"


def _layout(n: int) -> dict:
    """Fixed canvas geometry: self box left, choice nodes right."""
    n = max(1, int(n))
    width = PAD * 2 + BOX_W * 2 + GAP
    height = PAD * 2 + (n - 1) * ROW_H + BOX_H
    return {"width": width, "height": height,
            "x_self": PAD, "y_self": PAD + (n - 1) * ROW_H / 2,
            "x_node": PAD + BOX_W + GAP,
            "ys": [PAD + i * ROW_H for i in range(n)]}


def edges_svg(concept, choices, cid="bg") -> str:
    """SVG underlay: center box plus one arrow per choice.

    '' when the choices are not graphable. Never raises.
    """
    try:
        ok = _ok_list(choices)
        if not ok:
            return ""
        lay = _layout(len(ok))
        u = _uid(cid)
        self_l = _label(concept) or "self"
        parts = [
            f"<svg class='blastgraph' role='img' "
            f"aria-label='Dependency graph for {html.escape(self_l)}' "
            f"width='{lay['width']}' height='{lay['height']}' "
            f"viewBox='0 0 {lay['width']} {lay['height']}'>",
            f"<defs><marker id='bg-arrow-{u}' viewBox='0 0 10 10' "
            "refX='9' refY='5' markerWidth='7' markerHeight='7' "
            "orient='auto-start-reverse'>"
            "<path d='M0,0L10,5L0,10z' fill='currentColor'/>"
            "</marker></defs>",
            f"<title>What breaks if {html.escape(self_l)} changes</title>",
            f"<g class='bg-self'><rect x='{lay['x_self']}' "
            f"y='{lay['y_self']}' "
            f"width='{BOX_W}' height='{BOX_H}' rx='4'></rect>"
            f"<text x='{lay['x_self'] + BOX_W / 2}' "
            f"y='{lay['y_self'] + 15}' "
            f"text-anchor='middle'>{html.escape(self_l)}"
            f"<title>{html.escape(str(concept))}</title></text></g>",
        ]
        for i in range(len(ok)):
            y = lay["ys"][i]
            parts.append(
                f"<line x1='{lay['x_self'] + BOX_W}' "
                f"y1='{lay['y_self'] + BOX_H / 2}' "
                f"x2='{lay['x_node']}' y2='{y + BOX_H / 2}' "
                f"marker-end='url(#bg-arrow-{u})'/>")
        parts.append("</svg>")
        return "".join(parts)
    except Exception:  # noqa: BLE001 -- render must never raise
        return ""


def graph_html(concept, choices, cid="bg") -> str:
    """Clickable graph: edge SVG plus one submit button per choice node.

    Each node posts its full choice text as name='answer' through the
    caller's review form (labels may truncate; values never do).
    '' when the choices are not graphable. Never raises.
    """
    try:
        ok = _ok_list(choices)
        if not ok:
            return ""
        lay = _layout(len(ok))
        svg = edges_svg(concept, ok, cid)
        if not svg:
            return ""
        nodes = []
        for i, c in enumerate(ok):
            y = lay["ys"][i]
            nodes.append(
                f"<button name='answer' value='{html.escape(c)}' "
                f"class='bg-node' title='{html.escape(c)}' "
                f"style='position:absolute;left:{lay['x_node']}px;"
                f"top:{y}px;width:{BOX_W}px;height:{BOX_H}px;"
                f"overflow:hidden;white-space:nowrap;"
                f"text-overflow:ellipsis;padding:0 4px;"
                f"box-sizing:border-box'>{html.escape(_label(c))}</button>")
        return (
            f"<div class='bg-wrap' style='position:relative;"
            f"width:{lay['width']}px;height:{lay['height']}px;"
            f"max-width:100%'>{svg}{''.join(nodes)}</div>")
    except Exception:  # noqa: BLE001 -- render must never raise
        return ""


def legacy_html(choices) -> str:
    """Byte-identical copy of the cards.py flat-button row."""
    try:
        if not isinstance(choices, list):
            return ""
        return " ".join(
            f"<button name='answer' value='{html.escape(c)}'>"
            f"{html.escape(c)}</button>"
            for c in choices)
    except Exception:  # noqa: BLE001 -- render must never raise
        return ""


def branch_html(card, payload, cid) -> str:
    """Full etype-16 body: clickable graph, else legacy buttons."""
    try:
        from . import cards as cardsmod  # lazy: cards.py calls this branch
        conf = cardsmod._confidence()
    except Exception:  # noqa: BLE001 -- confidence must never raise
        conf = ""
    try:
        p = payload if isinstance(payload, dict) else {}
        ok = usable_choices(p)
        if ok:
            g = graph_html(concept_of(card), ok, cid)
            if g:
                return f"{g} {conf}"
        raw = p.get("choices", [])
        return f"{legacy_html(raw if isinstance(raw, list) else [])} {conf}"
    except Exception:  # noqa: BLE001 -- branch must never raise
        try:
            return f"<input name='answer' size='50' placeholder='Your answer'> {conf}"
        except Exception:  # noqa: BLE001 -- legacy must never raise
            return "<input name='answer' size='50'>"


def tour_entry() -> dict:
    """Tour registry entry for the clickable blast-radius graph."""
    return {"id": "blastgraph-clickable", "kind": "improvement",
            "title": "Clickable blast-radius graph",
            "blurb": "Blast-radius choices answer as nodes on a small graph.",
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection with a live sample graph."""
    try:
        sample = (graph_html("parse", ["load", "main", "cli"], "demo")
                  or legacy_html(["load", "main", "cli"]))
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Clickable blast-radius graph "
            "<small>(improvement)</small></h3>"
            "<p>Blast-radius cards (type 16) answer on a clickable graph from "
            "<code>groundwork/blastgraph.py</code> instead of a flat button row: "
            "the concept sits center, one node per stored choice fans out right, "
            "and each node posts the same answer value through the unchanged "
            "review form, so grading is untouched. Cards without usable choices "
            "keep the legacy buttons. A live sample renders below.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must never raise
        return (f"<h3 id='{STATUS_ANCHOR}'>Clickable blast-radius graph</h3>"
                "<p>Graph help temporarily unavailable.</p>")
