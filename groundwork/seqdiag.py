"""Sequence diagrams for 3-step call chains (I-127).

Type-10 exercises (``gen_call_path``) already store the ordered
entry-to-effect chain in ``payload["solution"]`` with a ``grounded``
flag. This module reuses that content as a lifelines-and-arrows
sequence diagram: one column per participant, directional arrows in
call order. Pure functions, stdlib only (``html``), no I/O, no DB
changes, never raises. Ungrounded or single-node chains render
nothing, so legacy pages stay byte-identical.

Caller path (real learner/reader, never a Status demo):
``cards.answer_widget`` prepends ``figure_html()`` to the type-10
(order-the-calls) widget — shared by the module page and the Due
queue — so the diagram sits above the order-the-calls prompt. Thin
delegation, one call site, no other edits.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b21-seqdiag"

MAX_PARTICIPANTS = 3
MAX_LABEL = 28
COL_W = 170


def chain_of(exercise) -> list:
    """Ordered type-10 chain from an exercise dict; [] when unusable."""
    try:
        if not isinstance(exercise, dict):
            return []
        payload = exercise.get("payload")
        if not isinstance(payload, dict):
            return []
        solution = payload.get("solution")
        if not isinstance(solution, list):
            return []
        return [s for s in solution if isinstance(s, str) and s.strip()]
    except Exception:  # noqa: BLE001 -- diagram lookup never raises
        return []


def participants(chain) -> list:
    """Cleaned participant labels in call order, capped at 3."""
    try:
        out = []
        for name in chain or []:
            if isinstance(name, str) and name.strip():
                out.append(name.strip())
            if len(out) >= MAX_PARTICIPANTS:
                break
        return out
    except Exception:  # noqa: BLE001 -- diagram lookup never raises
        return []


def _cx(i: int) -> int:
    """Lifeline x-center for column i."""
    return 10 + COL_W // 2 + i * COL_W


def sequence_svg(chain) -> str:
    """Lifelines-and-arrows SVG; "" when fewer than 2 participants."""
    labels = participants(chain)
    try:
        if len(labels) < 2:
            return ""
        n = len(labels)
        width = n * COL_W + 20
        height = 70 + (n - 1) * 30 + 34
        aria = html.escape(" then ".join(labels))
        parts = [
            f"<svg class='seq-diagram' viewBox='0 0 {width} {height}' "
            f"role='img' aria-label='sequence diagram of {aria}'>"]
        for i, label in enumerate(labels):
            cx = _cx(i)
            short = html.escape(label[:MAX_LABEL])
            parts.append(
                f"<rect x='{cx - 70}' y='8' width='140' height='30' "
                "rx='8' fill='var(--paper)' stroke='var(--ink)'/>"
                f"<text x='{cx}' y='28' text-anchor='middle' "
                f"font-size='13' fill='var(--ink)'>{short}</text>")
            parts.append(
                f"<line class='seq-life' x1='{cx}' y1='42' x2='{cx}' "
                f"y2='{height - 10}' stroke='var(--ink)' "
                "stroke-dasharray='5 4'/>")
        for i in range(n - 1):
            y = 70 + i * 30
            x1, x2 = _cx(i), _cx(i + 1) - 6
            parts.append(
                f"<line class='seq-call' x1='{x1}' y1='{y}' x2='{x2}' "
                f"y2='{y}' stroke='var(--ink)'/>"
                f"<polygon points='{x2},{y - 5} {x2},{y + 5} "
                f"{x2 + 6},{y}' fill='var(--ink)'/>")
            parts.append(
                f"<text x='{(x1 + x2) // 2}' y='{y - 6}' "
                f"text-anchor='middle' font-size='11' "
                f"fill='var(--ink)'>{i + 1}</text>")
        parts.append("</svg>")
        return "".join(parts)
    except Exception:  # noqa: BLE001 -- diagram builder never raises
        return ""


def figure_html(exercise, concept: str = "") -> str:
    """Captioned figure for a type-10 exercise; "" when no chain."""
    try:
        chain = participants(chain_of(exercise))
        svg = sequence_svg(chain)
        if not svg:
            return ""
        order = html.escape(" → ".join(chain))
        who = html.escape((concept or "this concept").strip()
                          or "this concept")
        return (
            f"<figure class='seq-figure'>{svg}"
            f"<figcaption>Call order through {who}: {order}.</figcaption>"
            "</figure>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Status-page subsection with a live 3-step sample."""
    try:
        sample = figure_html(
            {"type": 10,
             "payload": {"solution": ["handle_resize", "resize", "repaint"],
                         "grounded": True}},
            "resize")
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Call chains as sequence diagrams "
            "<small>(improvement)</small></h3>"
            "<p>Order-the-calls chains now draw as lifelines and arrows: "
            "<code>groundwork/seqdiag.py</code> reuses the type-10 "
            "<code>solution</code> chain on the lesson rendering path "
            "(<code>cards.answer_widget</code>); ungrounded chains render "
            "nothing. A live 3-step sample renders below.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must never raise
        return (f"<h3 id='{STATUS_ANCHOR}'>Call chains as sequence "
                "diagrams</h3>"
                "<p>Sequence-diagram help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "seqdiag-chains",
        "kind": "improvement",
        "title": "Call chains drawn as sequence diagrams",
        "blurb": "Order-the-calls chains draw as lifelines and arrows on the lesson page.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
