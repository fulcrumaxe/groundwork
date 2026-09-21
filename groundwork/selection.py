"""Selected-text accent (I-85): ``::selection`` matches the page accent.

Text selection still renders the browser default blue, unrelated to
the palette every page otherwise uses. This module owns the one
``::selection`` rule: the page accent (``--accent-due``, the same
token the briefing theme uses — no generic ``--accent`` exists)
with ink text, which the palette guarantees readable on accent
grounds. Forced-colors users keep their native selection via the
override. Raw declarations only, never ``<style>`` tags; pure
functions, stdlib only, no I/O, no DB changes.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b13-selection"

#: The only accent token selection may use (Batch 12 correction:
#: no generic --accent exists).
ACCENT_TOKEN = "--accent-due"


def selection_css() -> str:
    """Raw ``::selection`` declarations plus the forced-colors escape."""
    return (
        f"::selection{{background:var({ACCENT_TOKEN});color:var(--ink)}}"
        "@media(forced-colors:active){"
        "::selection{background:Highlight;color:HighlightText}}")


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Selection accent <small>(improvement)</small></h3>"
        "<p>Selected text now wears the page accent instead of the "
        "browser default blue: <code>groundwork/selection.py</code> "
        "provides <code>selection_css()</code> (one "
        "<code>::selection</code> rule on the real "
        "<code>--accent-due</code> token with ink text, wired into the "
        "head stylesheet), with a <code>forced-colors</code> override so "
        "high-contrast users keep native selection. Raw declarations "
        "only, never raises.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "selection-accent",
        "kind": "improvement",
        "title": "Selection accent",
        "blurb": "Selected text wears the page accent with ink text — forced-colors users keep native selection.",
        "path": "/status",
        "anchor": "status-b13-selection",
    }
