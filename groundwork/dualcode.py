"""Dual-coding packs (F-60): every key idea gets words + diagram + trace.

Cognitive science says a concept sticks when it arrives twice: once
as words, once as a picture. Lessons today are words plus an optional
trace, with no visual channel at all. This module owns the triple: a
plain-words line, an inline SVG box-and-arrow diagram (one box per
step, dependency-free, currentColor-free palette-safe fills), and a
worked trace table (step, state). Db-free library — the pipeline is
untouched; sections render the pack for one sample concept. Pure
functions, stdlib only (``html``), no I/O, no DB changes.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b13-dualcode"

MAX_STEPS = 8


def clean_steps(steps) -> list[str]:
    """Usable step labels: strings, stripped, non-empty, capped."""
    try:
        out = []
        for s in steps or []:
            if isinstance(s, str) and s.strip():
                out.append(s.strip())
            if len(out) >= MAX_STEPS:
                break
        return out
    except Exception:  # noqa: BLE001 -- pack builder must never raise
        return []


def diagram_svg(steps) -> str:
    """Box-and-arrow SVG: one rounded box per step, arrows between."""
    labels = clean_steps(steps)
    try:
        if not labels:
            return ""
        n = len(labels)
        w, bh, gap = 200, 34, 26
        h = n * (bh + gap) + 10
        parts = [f"<svg class='dual-diagram' viewBox='0 0 {w} {h}' "
                 f"role='img' aria-label='diagram of {n} steps'>"]
        y = 5
        for i, label in enumerate(labels):
            short = html.escape(label[:24])
            parts.append(
                f"<rect x='10' y='{y}' width='{w - 20}' height='{bh}' "
                "rx='8' fill='var(--paper)' stroke='var(--ink)'/>"
                f"<text x='{w // 2}' y='{y + 22}' text-anchor='middle' "
                f"font-size='13' fill='var(--ink)'>{short}</text>")
            if i < n - 1:
                parts.append(
                    f"<line x1='{w // 2}' y1='{y + bh}' x2='{w // 2}' "
                    f"y2='{y + bh + gap}' stroke='var(--ink)'/>"
                    f"<polygon points='{w // 2 - 5},{y + bh + gap - 8} "
                    f"{w // 2 + 5},{y + bh + gap - 8} {w // 2},{y + bh + gap}' "
                    "fill='var(--ink)'/>")
            y += bh + gap
        parts.append("</svg>")
        return "".join(parts)
    except Exception:  # noqa: BLE001 -- pack builder must never raise
        return ""


def trace_table(steps, states=None) -> str:
    """Worked trace: one row per step with its observable state."""
    labels = clean_steps(steps)
    try:
        states = list(states or [])
        rows = "".join(
            f"<tr><td>{i + 1}</td><td>{html.escape(label)}</td>"
            f"<td>{html.escape(str(states[i])) if i < len(states) else '—'}</td></tr>"
            for i, label in enumerate(labels))
        if not rows:
            return ""
        return ("<table class='log dual-trace'>"
                "<tr><th>Step</th><th>Does</th><th>State</th></tr>"
                f"{rows}</table>")
    except Exception:  # noqa: BLE001 -- pack builder must never raise
        return ""


def pack_html(concept: str = "", words: str = "",
              steps=None, states=None, wrapper: str = "article") -> str:
    """Full triple: words line + diagram + trace, all escaped.

    ``wrapper`` picks the outer tag; lesson rendering passes ``"div"``
    so packs nested inside card markup never inflate card counts.
    Unknown wrappers fail closed to ``article``.
    """
    try:
        tag = wrapper if wrapper in ("article", "div", "section") else "article"
        name = html.escape((concept or "this idea").strip()
                           or "this idea")
        prose = html.escape((words or "").strip())
        labels = clean_steps(steps)
        parts = [f"<{tag} class='dual-pack'><h4>{name}</h4>"]
        if prose:
            parts.append(f"<p class='dual-words'>{prose}</p>")
        svg = diagram_svg(labels)
        if svg:
            parts.append(svg)
        tbl = trace_table(labels, states)
        if tbl:
            parts.append(tbl)
        parts.append(f"</{tag}>")
        return "".join(parts)
    except Exception:  # noqa: BLE001 -- pack builder must never raise
        return "<article class='dual-pack'><h4>this idea</h4></article>"


def section_html() -> str:
    """Status-page subsection with a live sample pack."""
    sample = pack_html(
        "Retry with backoff",
        "Wait longer after each failure so a sick server can recover.",
        ["attempt the call", "sleep 1s on failure", "double the sleep",
         "give up after 5 tries"],
        ["ok or error", "slept 1s", "slept 2s", "raised last error"])
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Dual-coding packs <small>(feature)</small></h3>"
        "<p>Key ideas now arrive twice — words plus a picture: "
        "<code>groundwork/dualcode.py</code> provides "
        "<code>pack_html()</code> (plain-words line, dependency-free "
        "inline SVG box-and-arrow diagram, worked trace table), a "
        "db-free library the pipeline does not touch. A live pack for "
        "retry-with-backoff renders below.</p>" + sample)


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "dual-coding",
        "kind": "feature",
        "title": "Dual-coding packs",
        "blurb": "Every key idea gets words plus a diagram plus a worked trace — two channels, one concept.",
        "path": "/status",
        "anchor": "status-b13-dualcode",
    }
