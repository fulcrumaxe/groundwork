"""Stable Parsons drag-list space reserve (I-91).

Due-queue Parsons cards (exercise types 10/11) render `ol.parsons` whose
items hydrate/drag late, shifting the confidence pills and submit row
under the learner's finger. This module reserves `N * ROW_MIN_PX` of
vertical space on the list before first paint, so reorder only changes
`li` order — never page height.

Precedent: taptargets.py — one px token, `min-height` (never `height`)
so larger/wrapped content never clips. `parsons_css()` returns raw
declarations (never `<style>` tags); the head wire concatenates it next
to the existing `ol.parsons` rules in web.py. `block_html()` is a
drop-in for the cards.py etype 10/11 body fragment: with lines it adds
one inline `min-height` reserve on the `ol`; without lines it returns
the legacy string byte-identical (fallback pin). Pure functions, stdlib
only (html), no DB, never raise.
"""
from __future__ import annotations

import html

ROW_MIN_PX = 44  # aligns with taptargets MIN_PX: each row holds 2 buttons
STATUS_ANCHOR = "status-b18-parsons"

_MAX_ITEMS = 50


def _as_list(lines) -> list:
    """Lines as a list; anything non-list/tuple fails closed to []."""
    try:
        if isinstance(lines, (list, tuple)):
            return list(lines)
        return []
    except Exception:  # noqa: BLE001 — coercion must never raise
        return []


def reserve_px(lines) -> int:
    """Reserved list height in px: N * ROW_MIN_PX, clamped to _MAX_ITEMS."""
    try:
        n = len(_as_list(lines))
        if n < 1:
            return 0
        return min(n, _MAX_ITEMS) * ROW_MIN_PX
    except Exception:  # noqa: BLE001 — reserve must never raise
        return 0


def parsons_css() -> str:
    """Raw floor declarations for the head wire; never raises."""
    try:
        return (
            f"ol.parsons{{min-height:{ROW_MIN_PX}px}}"
            f"ol.parsons li{{min-height:{ROW_MIN_PX}px}}"
        )
    except Exception:  # noqa: BLE001 — CSS builder must never raise
        return "ol.parsons{}"


def list_html(cid, lines) -> str:
    """Stable `ol.parsons` for N lines; legacy bare `ol` when empty."""
    try:
        items = "".join(
            f"<li draggable='true' data-i='{i}'>"
            f"<span class='grip'>⠿</span> {html.escape(str(l))} "
            f"<button type='button' data-move='-1'>↑</button>"
            f"<button type='button' data-move='1'>↓</button></li>"
            for i, l in enumerate(_as_list(lines)))
        if not items:
            return f"<ol class='parsons' id='pl-{cid}'></ol>"
        px = reserve_px(lines)
        return (f"<ol class='parsons' id='pl-{cid}' "
                f"style='min-height:{px}px'>{items}</ol>")
    except Exception:  # noqa: BLE001 — renderer must never raise
        return f"<ol class='parsons' id='pl-{cid}'></ol>"


def block_html(cid, lines) -> str:
    """Drop-in for the cards.py etype 10/11 fragment (minus confidence).

    Non-empty lines: legacy paragraph + reserved `ol` + hidden answer +
    order label. Empty/missing lines: the exact legacy string cards.py
    emits today (items=""), so non-Parsons pages stay byte-identical.
    """
    try:
        ol = list_html(cid, lines)
        return (
            "<p>Drag the lines into order (or type the numbers):</p>"
            f"{ol}"
            f"<input type='hidden' name='answer' id='po-{cid}' value=''>"
            "<label>Order (numbers): "
            "<input name='answer_text' size='30' "
            "placeholder='0 1 2 …'></label> ")
    except Exception:  # noqa: BLE001 — block must never raise
        return ("<p>Drag the lines into order (or type the numbers):</p>"
                f"<ol class='parsons' id='pl-{cid}'></ol>"
                f"<input type='hidden' name='answer' id='po-{cid}' value=''>"
                "<label>Order (numbers): "
                "<input name='answer_text' size='30' "
                "placeholder='0 1 2 …'></label> ")


def tour_entry() -> dict:
    """Tour registry entry for the Parsons space reserve."""
    return {
        "id": "parsons-stable",
        "kind": "improvement",
        "title": "Stable Parsons drag lists",
        "blurb": ("Parsons code-order lists now reserve space for every "
                  "line before first paint — drag to reorder and the "
                  "submit row stays put. See the reserve below."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Parsons layout reserve "
        "<small>(improvement)</small></h3>"
        "<p>Parsons drag lists on Due cards reserve "
        f"<code>N&times;{ROW_MIN_PX}px</code> via an inline "
        "<code>min-height</code> on <code>ol.parsons</code> plus a CSS "
        "floor on the list and rows — <code>min-height</code>, never "
        "<code>height</code>, so wrapped lines never clip. "
        "<code>groundwork/parsons.py</code> provides "
        "<code>parsons_css()</code>, <code>list_html()</code> and "
        "<code>block_html()</code> (byte-identical legacy output when "
        "there are no lines).</p>"
    )
