"""Open Graph tags (I-88): shared module links unfurl with title + lede.

Shared Groundwork links paste as bare URLs: no ``og:title``,
``og:description``, or ``og:site_name`` exists in the head. This module
owns the unfurl tags: ``og_tags`` takes the same ``(title, lede)``
``page()`` already renders (module pages pass their lede through, so
shares name the concept being studied), escapes both, and emits the
minimal set readers need — title, type, site name, description.
``og:url`` stays out on purpose: the app is usually localhost, and a
localhost canonical URL in a share card is a lie. Pure functions,
stdlib only (``html``), no I/O, no DB changes.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b13-ogtags"

SITE_NAME = "Groundwork"
DEFAULT_DESCRIPTION = ("A code learning companion: study modules, "
                       "practice with exercises, own the material.")


def og_tags(title: str = "", lede: str = "") -> str:
    """Head meta tags for link unfurls; never emits raw input."""
    try:
        name = (title or "").strip() or SITE_NAME
        desc = (lede or "").strip() or DEFAULT_DESCRIPTION
        # One line of plain text: tags and newlines never unfurl well.
        desc = " ".join(desc.split())
        if len(desc) > 300:
            desc = desc[:297] + "..."
        return (
            f"<meta property='og:title' content='{html.escape(name, True)}'>"
            "<meta property='og:type' content='website'>"
            f"<meta property='og:site_name' content='{SITE_NAME}'>"
            f"<meta property='og:description' content='{html.escape(desc, True)}'>")
    except Exception:  # noqa: BLE001 -- head wire must never raise
        return ("<meta property='og:title' content='Groundwork'>"
                "<meta property='og:type' content='website'>"
                f"<meta property='og:site_name' content='{SITE_NAME}'>")


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Share unfurls <small>(improvement)</small></h3>"
        "<p>Shared links now unfurl with a title and summary: "
        "<code>groundwork/ogtags.py</code> provides "
        "<code>og_tags()</code> (title, type, site name, and the page "
        "lede as description, all escaped and length-capped, wired into "
        "the head on every page). No <code>og:url</code> on purpose — "
        "the app usually serves localhost, and a localhost canonical "
        "URL in a share card would be a lie. Never raises.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "share-unfurls",
        "kind": "improvement",
        "title": "Share unfurls",
        "blurb": "Shared links unfurl with the page title and lede — no bare URLs, no localhost canonical lie.",
        "path": "/status",
        "anchor": "status-b13-ogtags",
    }
