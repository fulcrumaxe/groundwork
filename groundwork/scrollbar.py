"""Platform-respecting scrollbars (I-86): thin palette-matched scrollbars.

Scrollbars still render the browser default while every other control
follows the palette. This module owns the scrollbar rules: Firefox
gets ``scrollbar-width: thin`` plus ``scrollbar-color`` on the real
``--stale``/``--paper`` tokens (the muted pair — a scrollbar must not
shout the page accent), WebKit gets the matching pseudo-element set,
and platforms that opt out keep natives: ``forced-colors`` resets to
``auto``, and coarse-pointer (touch) devices skip the thin rule so
tap-sized scrolling stays usable. Raw declarations only, never
``<style>`` tags; pure functions, stdlib only, no I/O, no DB changes.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b13-scrollbar"


def scrollbar_css() -> str:
    """Raw scrollbar declarations for Firefox, WebKit, and opt-outs."""
    return (
        "*{scrollbar-width:thin;scrollbar-color:var(--stale) var(--paper)}"
        "::-webkit-scrollbar{width:10px;height:10px}"
        "::-webkit-scrollbar-track{background:var(--paper)}"
        "::-webkit-scrollbar-thumb{background:var(--stale);"
        "border-radius:5px;border:2px solid var(--paper)}"
        "@media(pointer:coarse){*{scrollbar-width:auto}}"
        "@media(forced-colors:active){*{scrollbar-color:auto}}")


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Palette scrollbars <small>(improvement)</small></h3>"
        "<p>Scrollbars now match the palette instead of the browser "
        "default: <code>groundwork/scrollbar.py</code> provides "
        "<code>scrollbar_css()</code> (thin muted pair on the real "
        "<code>--stale</code>/<code>--paper</code> tokens for Firefox "
        "and WebKit, wired into the head stylesheet), while "
        "touch devices keep full-size scrolling and forced-colors users "
        "keep native scrollbars. Raw declarations only, never raises.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "palette-scrollbars",
        "kind": "improvement",
        "title": "Palette scrollbars",
        "blurb": "Thin palette-matched scrollbars — touch devices and forced-colors users keep natives.",
        "path": "/status",
        "anchor": "status-b13-scrollbar",
    }
