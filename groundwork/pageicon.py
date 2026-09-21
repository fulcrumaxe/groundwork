"""Favicon per page state (I-87): the tab icon carries the due count.

Every page serves the same static mark, so a tab never says whether
cards are waiting. This module owns the state-aware icon: the ink
rounded square from ``favicon.py`` gains a paper count badge (capped
at "99+"), emitted as an SVG data URI so no new route or asset is
needed. ``link_tag`` reads the same ``counts`` dict ``page()``
already receives (missing/zero means the plain mark), and the head
wire embeds it on every page. Pure functions, stdlib only
(``urllib.parse``), no I/O, no DB changes.
"""
from __future__ import annotations

from urllib.parse import quote

STATUS_ANCHOR = "status-b13-pageicon"

LINK_ID = "gw-icon"
MAX_BADGE = 99


def badge_text(due) -> str:
    """Badge label for a due count: "" when zero, capped at 99+."""
    try:
        n = int(due)
    except Exception:  # noqa: BLE001 -- icon lookup must never raise
        return ""
    if n <= 0:
        return ""
    if n > MAX_BADGE:
        return "99+"
    return str(n)


def icon_svg(due=0) -> str:
    """Ink rounded square with paper G, plus an optional count badge."""
    label = badge_text(due)
    badge = ""
    if label:
        # Wide pill for 2-3 chars, circle for one.
        wide = len(label) > 1
        w = "30" if wide else "20"
        badge = (
            f"<rect x='40' y='2' width='{w}' height='20' rx='10' "
            "fill='#a00'/>"
            f"<text x='{'55' if wide else '50'}' y='17' font-size='13' "
            "text-anchor='middle' fill='#fff' "
            f"font-family='Georgia,serif'>{label}</text>")
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
        "<rect width='64' height='64' rx='12' fill='#1a1a1a'/>"
        "<text x='32' y='44' font-size='36' text-anchor='middle' "
        "fill='#fff' font-family='Georgia,serif'>G</text>"
        f"{badge}</svg>")


def icon_data_uri(due=0) -> str:
    """``icon_svg`` as a ``data:image/svg+xml`` URI (link-ready)."""
    try:
        return "data:image/svg+xml," + quote(icon_svg(due), safe="")
    except Exception:  # noqa: BLE001 -- icon lookup must never raise
        return "data:image/svg+xml," + quote(icon_svg(0), safe="")


def link_tag(counts=None) -> str:
    """Head ``<link rel='icon'>`` for this page's due count.

    ``counts`` is the nav-counts dict (or None in tests); anything
    unreadable means the plain mark, never a raise.
    """
    try:
        due = 0
        if isinstance(counts, dict):
            due = counts.get("due", 0)
        uri = icon_data_uri(due)
    except Exception:  # noqa: BLE001 -- head wire must never raise
        uri = icon_data_uri(0)
    return f"<link id='{LINK_ID}' rel='icon' href=\"{uri}\">"


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Due-count favicon <small>(improvement)</small></h3>"
        "<p>The tab icon now says whether cards are waiting: "
        "<code>groundwork/pageicon.py</code> provides "
        "<code>icon_data_uri()</code> (the ink-G mark plus a paper count "
        "badge capped at 99+, URL-encoded as an SVG data URI — no new "
        "route, no asset) and <code>link_tag()</code> over the nav "
        "counts the head wire already receives, embedded on every page. "
        "Helpers fail closed, never raise.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "due-favicon",
        "kind": "improvement",
        "title": "Due-count favicon",
        "blurb": "The tab icon carries the live due count as a badge — zero means the plain mark.",
        "path": "/status",
        "anchor": "status-b13-pageicon",
    }
