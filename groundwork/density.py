"""Compact density toggle (I-89): small screens get a denser page.

One fixed type scale and spacing rhythm serve phones and desktops
alike, so small screens scroll far. This module owns the density
switch: ``[data-density='compact']`` overrides shrink section gaps
and body text (referencing only real ``--sp-*``/``--fs-*`` tokens),
``toggle_js`` persists the choice in ``localStorage`` (no-JS browsers
simply keep the comfortable default), and ``toggle_html`` is the
header button the head wire embeds on every page. ``tap-min`` floors
stay untouched — compact never shrinks tap targets. Raw declarations
only, never ``<style>`` tags; stdlib only (``re``), no I/O, no DB.
"""
from __future__ import annotations

import re

STATUS_ANCHOR = "status-b13-density"

STORE_KEY = "gw-density"
ATTR = "data-density"
COMPACT = "compact"
TOGGLE_ID = "gw-density-toggle"


def density_css() -> str:
    """Raw compact-density overrides plus the toggle's own shape."""
    return (
        f"html[{ATTR}='{COMPACT}']{{--sp-section:.6rem;--sp-snug:.45rem}}"
        f"html[{ATTR}='{COMPACT}'] body{{font-size:var(--fs-small)}}"
        f"html[{ATTR}='{COMPACT}'] h1{{font-size:var(--fs-h2)}}"
        f"#{TOGGLE_ID}{{font-size:.8rem;padding:.3rem .6rem;"
        "border:1px solid var(--stale);border-radius:var(--r-control);"
        "background:var(--paper);color:var(--ink);cursor:pointer}")


def toggle_js() -> str:
    """Density switch: read stored choice, toggle on click, persist.

    Presentation only: no ``fetch``, no cookies, no server round trip.
    Without JS the button does nothing and comfortable stays on.
    """
    return (
        "<script data-density-toggle>"
        "(function(){"
        "try{"
        "var root=document.documentElement;"
        "try{if(localStorage.getItem(\"" + STORE_KEY + "\")===\"" + COMPACT + "\")"
        "root.setAttribute(\"" + ATTR + "\",\"" + COMPACT + "\");}catch(e){}"
        "var b=document.getElementById(\"" + TOGGLE_ID + "\");"
        "if(!b||!b.addEventListener)return;"
        "b.addEventListener(\"click\",function(){"
        "var cur=root.getAttribute(\"" + ATTR + "\")===\"" + COMPACT + "\";"
        "try{"
        "if(cur){root.removeAttribute(\"" + ATTR + "\");"
        "localStorage.removeItem(\"" + STORE_KEY + "\");"
        "b.textContent=\"Compact\";}"
        "else{root.setAttribute(\"" + ATTR + "\",\"" + COMPACT + "\");"
        "localStorage.setItem(\"" + STORE_KEY + "\",\"" + COMPACT + "\");"
        "b.textContent=\"Comfortable\";}"
        "}catch(e){}});}catch(e){}"
        "})();</script>")


def toggle_html() -> str:
    """Header button; label names the action, not the state."""
    return (f"<button id='{TOGGLE_ID}' type='button' "
            "title='Toggle compact density'>Compact</button>")


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Compact density <small>(improvement)</small></h3>"
        "<p>Small screens get a denser page on demand: "
        "<code>groundwork/density.py</code> provides "
        "<code>density_css()</code> (a <code>data-density</code> "
        "override shrinking section gaps and body text off the real "
        "scale tokens — tap floors untouched), "
        "<code>toggle_js()</code> (a <code>localStorage</code> switch, "
        "no server round trip), and <code>toggle_html()</code> (the "
        "header button on every page). Helpers fail closed, never "
        "raise.</p>"
        + toggle_html())


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "density-toggle",
        "kind": "improvement",
        "title": "Compact density",
        "blurb": "One header button shrinks gaps and type for small screens — tap targets stay full-size.",
        "path": "/status",
        "anchor": "status-b13-density",
    }
