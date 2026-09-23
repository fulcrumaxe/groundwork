"""Horizontally scrollable data tables with sticky first column (I-92).

Wide `<table class='log'>` grids (History accuracy/timeline tables,
Status audit tables) overflow 360px viewports: the responsive audit
(I-90, `groundwork/responsive.py:narrow_css`) shrinks table text but
cannot fit five columns into a phone. This module owns the fix:
`wrap_table` puts wide tables in a sideways scroll container and
`scroll_css` pins the first column so row labels stay visible while
panning. Raw declarations only, never `<style>` tags.

Caller path (real learner/reader, never a Status demo or fixture):
`groundwork/history.py:history_html`, served by
`groundwork/web.py:Handler.do_GET` on the History page. Its Skill /
Date / Day `<table class='log'>` grids are the wide tables this wraps.

Behavioral-effect test idea: a History page with review data renders
its log table inside `<div class="tscroll">` with the label column
stuck; legacy no-data fallback — an empty History (no reviews) renders
no wrapper at all (`wrap_table("")` returns `""` unchanged).
"""
from __future__ import annotations

import re

STATUS_ANCHOR = "status-b21-tablescroll"

#: Tables with at least this many columns get a scroll container.
#: Two columns already fit a 360px phone; wrapping them would add a
#: useless scroll region.
WRAP_MIN_COLS = 3

#: Scroll-container class applied by `wrap_table` and styled by
#: `scroll_css`. Single class so the head-stylesheet wiring is one
#: concatenation term.
CONTAINER_CLASS = "tscroll"

_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
_CELL_RE = re.compile(r"<t[hd][\s>]", re.IGNORECASE)


def column_count(table_html: str = "") -> int:
    """Cells in the table's first row; 0 for anything unparseable.

    Never raises: non-strings, empty strings, and tables without rows
    all yield 0 (legacy no-data tables simply never qualify).
    """
    try:
        if not isinstance(table_html, str) or not table_html:
            return 0
        m = _ROW_RE.search(table_html)
        if not m:
            return 0
        return len(_CELL_RE.findall(m.group(1)))
    except Exception:  # noqa: BLE001 -- audit must never raise
        return 0


def needs_wrap(table_html: str = "") -> bool:
    """True when the table is wide enough to need a scroll container."""
    try:
        return column_count(table_html) >= WRAP_MIN_COLS
    except Exception:  # noqa: BLE001 -- audit must never raise
        return False


def wrap_table(table_html: str = "") -> str:
    """Wrap a wide table in the scroll container; else return unchanged.

    Narrow tables (< WRAP_MIN_COLS columns), empty/missing markup, and
    already-wrapped tables pass through untouched, so the legacy
    no-data History (no rows, no table) renders exactly as before with
    no empty scroll region. Idempotent: wrapping twice never nests.
    """
    try:
        if not isinstance(table_html, str) or not table_html:
            return table_html
        if CONTAINER_CLASS in table_html:
            return table_html
        if not needs_wrap(table_html):
            return table_html
        return f'<div class="{CONTAINER_CLASS}">{table_html}</div>'
    except Exception:  # noqa: BLE001 -- render must never raise
        return table_html


def scroll_css() -> str:
    """Raw scroll-container plus sticky-first-column declarations.

    The container pans sideways (`separate` border model so sticky
    cells keep their background while sliding under); first-column
    header and body cells stick at left zero on the real `--paper`
    token (a scrolled column sliding under bare text would be
    unreadable) above the panning cells. Desktop untouched: rules only
    size the wrapper, never the page.
    """
    return (
        f".{CONTAINER_CLASS}{{overflow-x:auto;max-width:100%}}"
        f".{CONTAINER_CLASS} table{{border-collapse:separate;"
        "border-spacing:0}"
        f".{CONTAINER_CLASS} th:first-child,"
        f".{CONTAINER_CLASS} td:first-child{{position:sticky;left:0;"
        "background:var(--paper);z-index:1}}")


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Scrollable tables "
            "<small>(improvement)</small></h3>"
            "<p>Wide data tables pan sideways instead of overflowing "
            "phones: <code>groundwork/tablescroll.py</code> provides "
            "<code>wrap_table()</code> (scroll container for tables of "
            "three-plus columns, wired into the History log tables) and "
            "<code>scroll_css()</code> (sideways panning with the first "
            "column stuck at the left on <code>--paper</code> so row "
            "labels stay visible). Narrow tables and the legacy no-data "
            "History pass through unwrapped. Raw declarations only, "
            "never raises.</p>")
    except Exception:  # noqa: BLE001 -- status must never raise
        return (f"<h3 id='{STATUS_ANCHOR}'>Scrollable tables</h3>"
                "<p>Table help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "scrollable-tables",
        "kind": "improvement",
        "title": "Scrollable tables",
        "blurb": "Wide tables pan sideways on phones with the first column stuck — row labels stay visible while scrolling.",
        "path": "/status",
        "anchor": "status-b21-tablescroll",
    }
