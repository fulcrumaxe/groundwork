"""Rabbit-hole mode (F-136): curiosity-driven free explore, tracked by URL.

The visited-concept chain rides in ?trail=a>b>c (no tables, no schema
change). trail_html renders the breadcrumb + depth marker; wander_html
adds "wander further" caller/callee links that extend the chain. Bonus
exploration only: never duty, zero grading impact. Pure, stdlib-only,
never raises; empty trail renders "" so pages keep legacy bytes.
"""
from __future__ import annotations

import html
from urllib.parse import quote

from .lessons import slug as lesson_slug

STATUS_ANCHOR = "status-b25-rabbithole"
MAX_DEPTH = 8


def parse_trail(raw) -> list:
    """?trail= value -> cleaned name chain, capped; [] when none/hostile."""
    try:
        if not isinstance(raw, str) or not raw.strip():
            return []
        out = []
        for bit in raw.split(">"):
            bit = bit.strip().split(":")[-1].strip()
            if bit and bit not in out:
                out.append(bit)
            if len(out) >= MAX_DEPTH:
                break
        return out
    except Exception:  # noqa: BLE001 -- parse must never raise
        return []


def trail_qs(trail) -> str:
    """Chain -> quoted ?trail= value; "" when empty."""
    try:
        return quote(">".join(trail or []), safe=">")
    except Exception:  # noqa: BLE001 -- quote must never raise
        return ""


def trail_html(raw, mid: str = "") -> str:
    """Breadcrumb + depth + exit; "" with no trail (legacy path)."""
    try:
        trail = parse_trail(raw)
        if not trail:
            return ""
        crumbs = []
        for i, name in enumerate(trail):
            q = trail_qs(trail[: i + 1])
            crumbs.append(
                f"<a href='/modules/{html.escape(str(mid), True)}?trail={q}"
                f"#lesson-{html.escape(lesson_slug(name), True)}'>"
                f"{html.escape(name)}</a>")
        return (
            "<nav class='rabbithole' id='rabbithole' aria-label='Rabbit-hole trail'>"
            f"<small>Rabbit hole (depth {len(trail)}"
            f"{'+' if len(trail) >= MAX_DEPTH else ''}): "
            + " › ".join(crumbs) +
            f" · <a href='/modules/{html.escape(str(mid), True)}'>climb out</a>"
            " · bonus wander, never duty, no grading impact</small></nav>")
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def _names(lesson) -> tuple:
    try:
        return ([n for n in (lesson.get("callers") or []) if isinstance(n, str)],
                [n for n in (lesson.get("callees") or []) if isinstance(n, str)])
    except Exception:  # noqa: BLE001 -- read must never raise
        return ([], [])


def wander_html(lesson, raw, mid: str = "", known=()) -> str:
    """Wander-further links extending the chain; "" when no trail/data."""
    try:
        trail = parse_trail(raw)
        if not trail or not isinstance(lesson, dict):
            return ""
        have = {lesson_slug(k) for k in (known or []) if k}
        links = []
        for n in sum(_names(lesson), []):
            short = n.strip().split(":")[-1].strip()
            if not short or lesson_slug(short) not in have or short in trail:
                continue
            q = trail_qs(trail + [short])
            links.append(
                f"<a href='/modules/{html.escape(str(mid), True)}?trail={q}"
                f"#lesson-{html.escape(lesson_slug(short), True)}'>"
                f"{html.escape(short)}</a>")
            if len(links) >= 5:
                break
        if not links:
            return ""
        return ("<p class='wander'><small>Wander further (bonus): "
                + " · ".join(links) + "</small></p>")
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def tour_entry() -> dict:
    """Tour registry entry for rabbit-hole mode."""
    return {"id": "rabbit-hole", "kind": "feature",
            "title": "Rabbit-hole mode",
            "blurb": ("Follow caller links freely across lessons with a "
                      "visible breadcrumb trail — bonus, never duty."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection with live sample; joined by batch25."""
    try:
        sample = trail_html("add>total", "m1")
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Rabbit-hole mode <small>(feature)</small></h3>"
            "<p>Follow caller/callee links freely across lessons with a visible "
            "breadcrumb trail carried in <code>?trail=</code> — no new tables, "
            "no grading impact, bonus never duty. "
            "<code>groundwork/rabbithole.py</code> renders on the module path "
            "(<code>Handler.module_html</code>); pages without a trail render "
            "exactly as before. A live sample renders below.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Rabbit-hole mode</h3>"
                "<p>Trail help temporarily unavailable.</p>")
